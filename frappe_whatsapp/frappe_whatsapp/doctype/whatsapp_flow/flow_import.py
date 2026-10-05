# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Bring flows that exist on WhatsApp into WhatsApp Flow."""

import json

import frappe
import requests
from frappe import _

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_graph import (
	fetch_flow_json,
	get_flow_api,
	get_flow_details,
)
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_rows import add_screens_from_json
from frappe_whatsapp.utils.meta_api import get_graph_url


def list_meta_flows(account_name):
	"""
	All flows of a WhatsApp Business Account, marked with whether they exist here.

	Parameters:
		account_name (str, required): WhatsApp Account name.

	Returns:
		list: Flows from Meta, each with "exists_locally" and "local_name" added.
	"""
	try:
		flows = get_meta_flows(account_name)
	except Exception as e:
		frappe.throw(_("Failed to fetch flows: {0}").format(str(e)))

	for flow in flows:
		existing = frappe.db.exists("WhatsApp Flow", {"flow_id": flow["id"]})
		flow["exists_locally"] = bool(existing)
		flow["local_name"] = existing or None

	return flows


def import_flow(account_name, flow_id, flow_name=None):
	"""
	Create a WhatsApp Flow from a flow on WhatsApp, with its screens and fields.

	Parameters:
		account_name (str, required): WhatsApp Account name.
		flow_id (str, required): WhatsApp flow id.
		flow_name (str, optional): Local name; defaults to the name on WhatsApp.

	Returns:
		str: Name of the new WhatsApp Flow.
	"""
	existing = frappe.db.exists("WhatsApp Flow", {"flow_id": flow_id})
	if existing:
		frappe.throw(_("Flow already exists: {0}").format(existing))

	try:
		data = get_flow_details(account_name, flow_id, "id,name,status,categories,json_version,preview")
		flow = frappe.get_doc(
			{
				"doctype": "WhatsApp Flow",
				"flow_name": flow_name or data.get("name", f"Imported Flow {flow_id}"),
				"whatsapp_account": account_name,
				"flow_id": flow_id,
				"status": data.get("status", "Draft").title(),
				"category": data["categories"][0] if data.get("categories") else "OTHER",
				"data_api_version": data.get("json_version", "6.0"),
				"preview_url": data.get("preview", {}).get("preview_url", ""),
			}
		)

		flow_json = fetch_flow_json(account_name, flow_id)
		if flow_json:
			flow.flow_json = json.dumps(flow_json, indent=2)
			add_screens_from_json(flow, flow_json)

		# An imported flow may have no screens yet, so the usual checks are skipped.
		flow.flags.ignore_validate = True
		flow.insert(ignore_permissions=True)

		frappe.msgprint(_("Flow imported successfully: {0}").format(flow.name), indicator="green")
		return flow.name
	except Exception as e:
		frappe.throw(_("Failed to import flow: {0}").format(str(e)))


def sync_all_flows(account_name):
	"""
	Import new flows from WhatsApp and refresh the ones that already exist here.

	One failing flow is logged and counted as skipped; the rest still sync.

	Parameters:
		account_name (str, required): WhatsApp Account name.

	Returns:
		dict: {"imported": int, "updated": int, "skipped": int}
	"""
	try:
		flows = get_meta_flows(account_name)
	except Exception as e:
		frappe.throw(_("Failed to sync flows: {0}").format(str(e)))

	result = {"imported": 0, "updated": 0, "skipped": 0}
	for meta_flow in flows:
		existing = frappe.db.exists("WhatsApp Flow", {"flow_id": meta_flow.get("id")})
		try:
			if existing:
				update_local_flow(existing, meta_flow, account_name)
				result["updated"] += 1
			else:
				create_local_flow(meta_flow, account_name)
				result["imported"] += 1
		except Exception as e:
			action = "update" if existing else "import"
			frappe.log_error(f"Failed to {action} flow {meta_flow.get('id')}: {str(e)}")
			result["skipped"] += 1

	return result


def update_local_flow(flow_name, meta_flow, account_name):
	"""
	Refresh an existing WhatsApp Flow's status, category, screens and fields from WhatsApp.

	Parameters:
		flow_name (str, required): Local WhatsApp Flow name.
		meta_flow (dict, required): Flow from Meta's list.
		account_name (str, required): WhatsApp Account name.

	Returns:
		None
	"""
	flow = frappe.get_doc("WhatsApp Flow", flow_name)
	flow.status = meta_flow.get("status", "Draft").title()
	if meta_flow.get("categories"):
		flow.category = meta_flow["categories"][0]

	flow_json = fetch_flow_json(account_name, meta_flow.get("id"))
	if flow_json:
		flow.flow_json = json.dumps(flow_json, indent=2)
		flow.data_api_version = flow_json.get("version", "6.0")
		flow.screens = []
		flow.fields = []
		add_screens_from_json(flow, flow_json)

	flow.flags.ignore_validate = True
	flow.save(ignore_permissions=True)


def create_local_flow(meta_flow, account_name):
	"""
	Create a WhatsApp Flow for a flow found on WhatsApp.

	Parameters:
		meta_flow (dict, required): Flow from Meta's list.
		account_name (str, required): WhatsApp Account name.

	Returns:
		None
	"""
	flow_id = meta_flow.get("id")
	flow = frappe.get_doc(
		{
			"doctype": "WhatsApp Flow",
			"flow_name": meta_flow.get("name") or f"Flow {flow_id}",
			"whatsapp_account": account_name,
			"flow_id": flow_id,
			"status": meta_flow.get("status", "Draft").title(),
			"category": meta_flow["categories"][0] if meta_flow.get("categories") else "OTHER",
		}
	)

	flow_json = fetch_flow_json(account_name, flow_id)
	if flow_json:
		flow.flow_json = json.dumps(flow_json, indent=2)
		flow.data_api_version = flow_json.get("version", "6.0")
		add_screens_from_json(flow, flow_json)

	flow.flags.ignore_validate = True
	flow.insert(ignore_permissions=True)


def get_meta_flows(account_name):
	"""
	List the business account's flows from the Graph API.

	Parameters:
		account_name (str, required): WhatsApp Account name.

	Returns:
		list: [{"id", "name", "status", "categories"}]
	"""
	account, headers = get_flow_api(account_name)
	response = requests.get(
		get_graph_url(account, f"{account.business_id}/flows?fields=id,name,status,categories"), headers=headers
	)
	response.raise_for_status()
	return response.json().get("data", [])
