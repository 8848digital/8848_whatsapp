# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Read a WhatsApp Flow's status, preview link and details back from Meta."""

import json

import frappe
from frappe import _

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_graph import fetch_flow_json, get_flow_details
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_meta import require_flow_id

STATUS_FIELDS = "id,name,status,categories,validation_errors,json_version,data_api_version,data_channel_uri,preview,whatsapp_business_account"
SYNC_FIELDS = "id,name,status,categories,json_version,preview"


def get_preview_url(flow):
	"""
	Get (and store) the web preview link of the flow.

	Parameters:
		flow (Document, required): WhatsApp Flow.

	Returns:
		str: Preview URL.
	"""
	require_flow_id(flow)
	try:
		data = get_flow_details(flow.whatsapp_account, flow.flow_id, "preview.invalidate(false)")
		preview_url = data.get("preview", {}).get("preview_url")
		if not preview_url:
			frappe.throw(_("Preview URL not available"))

		flow.preview_url = preview_url
		flow.save()
		return preview_url
	except Exception as e:
		frappe.throw(_("Failed to get preview: {0}").format(str(e)))


def get_flow_status(flow):
	"""
	Read the flow's status and validation errors from WhatsApp and show them.

	Parameters:
		flow (Document, required): WhatsApp Flow.

	Returns:
		dict: Flow details from Meta.
	"""
	require_flow_id(flow)
	try:
		data = get_flow_details(flow.whatsapp_account, flow.flow_id, STATUS_FIELDS)
		if data.get("status"):
			flow.status = data["status"].title()
			flow.save()

		show_flow_status(data)
		return data
	except Exception as e:
		frappe.throw(_("Failed to get flow status: {0}").format(str(e)))


def show_flow_status(data):
	"""
	Show Meta's validation errors, or the flow's status and JSON version.

	Parameters:
		data (dict, required): Flow details from Meta.

	Returns:
		None
	"""
	validation_errors = data.get("validation_errors", [])
	if validation_errors:
		lines = []
		for error in validation_errors:
			lines.append(f"- {error.get('error', 'Unknown error')} at {error.get('error_type', 'unknown')}")
		frappe.msgprint(
			_("Flow Validation Errors:\n{0}").format("\n".join(lines)), title=_("Validation Errors"), indicator="red"
		)
		return

	frappe.msgprint(
		_("Flow Status: {0}\nJSON Version: {1}").format(data.get("status", "Unknown"), data.get("json_version", "Unknown")),
		title=_("Flow Status"),
		indicator="green" if data.get("status") == "PUBLISHED" else "blue",
	)


def sync_flow_from_meta(flow):
	"""
	Copy status, category, JSON version, preview link and Flow JSON from WhatsApp.

	Parameters:
		flow (Document, required): WhatsApp Flow with a flow_id.

	Returns:
		dict: Flow details from Meta.
	"""
	if not flow.flow_id:
		frappe.throw(_("Flow ID is required to sync"))

	try:
		data = get_flow_details(flow.whatsapp_account, flow.flow_id, SYNC_FIELDS)
		if data.get("status"):
			flow.status = data["status"].title()
		if data.get("categories"):
			flow.category = data["categories"][0]
		if data.get("json_version"):
			flow.data_api_version = data["json_version"]
		if data.get("preview", {}).get("preview_url"):
			flow.preview_url = data["preview"]["preview_url"]

		flow_json = fetch_flow_json(flow.whatsapp_account, flow.flow_id)
		if flow_json:
			flow.flow_json = json.dumps(flow_json, indent=2)

		flow.save()
		frappe.msgprint(_("Flow synced successfully from WhatsApp"), indicator="green")
		return data
	except Exception as e:
		frappe.throw(_("Failed to sync flow: {0}").format(str(e)))
