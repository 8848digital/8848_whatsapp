# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Create, publish and manage one WhatsApp Flow on Meta."""

import json

import frappe
import requests
from frappe import _
from frappe.integrations.utils import make_post_request

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_builder import generate_flow_json
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_graph import get_flow_api
from frappe_whatsapp.utils.meta_api import get_graph_url

def load_flow(flow_name):
	"""
	Load a WhatsApp Flow the user can read, for the flow actions in api/v1/flow.py.

	Parameters:
		flow_name (str, required): WhatsApp Flow name.

	Returns:
		Document: The WhatsApp Flow.
	"""
	flow = frappe.get_doc("WhatsApp Flow", flow_name)
	flow.check_permission("read")
	return flow


def create_flow_on_meta(flow):
	"""
	Create the flow on WhatsApp, then upload its JSON.

	Parameters:
		flow (Document, required): WhatsApp Flow without a flow_id yet.

	Returns:
		None
	"""
	if flow.flow_id:
		frappe.throw(_("Flow already exists on WhatsApp. Use update instead."))

	account, headers = get_flow_api(flow.whatsapp_account)
	payload = {"name": flow.flow_name, "categories": [flow.category]}

	try:
		response = make_post_request(
			get_graph_url(account, f"{account.business_id}/flows"),
			headers=dict(headers, **{"Content-Type": "application/json"}),
			data=json.dumps(payload),
		)
		flow.flow_id = response.get("id")
		flow.save()

		upload_flow_json(flow)
		frappe.msgprint(_("Flow created successfully on WhatsApp"))
	except Exception as e:
		frappe.throw(_("Failed to create flow: {0}").format(str(e)))


def upload_flow_json(flow):
	"""
	Upload the freshly generated Flow JSON as the flow's "flow.json" asset.

	Parameters:
		flow (Document, required): WhatsApp Flow with a flow_id.

	Returns:
		None
	"""
	require_flow_id(flow)
	account, headers = get_flow_api(flow.whatsapp_account)
	files = {
		"file": ("flow.json", json.dumps(generate_flow_json(flow)), "application/json"),
		"name": (None, "flow.json"),
		"asset_type": (None, "FLOW_JSON"),
	}

	try:
		response = requests.post(get_graph_url(account, f"{flow.flow_id}/assets"), headers=headers, files=files)
	except requests.exceptions.RequestException as e:
		frappe.throw(_("Failed to upload flow JSON: {0}").format(str(e)))

	if response.status_code != 200:
		error = response.json().get("error", {})
		error_message = error.get("message", response.text)
		# Meta puts the useful validation detail in error_user_msg.
		if error.get("error_user_msg"):
			error_message = f"{error_message} - {error['error_user_msg']}"
		frappe.throw(_("Failed to upload flow JSON: {0}").format(error_message))

	frappe.msgprint(_("Flow JSON uploaded successfully"))


def publish_flow(flow):
	"""
	Publish the flow so it can be sent to customers. Published flows can't be edited.

	Parameters:
		flow (Document, required): WhatsApp Flow.

	Returns:
		None
	"""
	require_flow_id(flow)
	if flow.status == "Published":
		frappe.throw(_("Flow is already published"))

	account, headers = get_flow_api(flow.whatsapp_account)
	try:
		response = requests.post(
			get_graph_url(account, f"{flow.flow_id}/publish"),
			headers=dict(headers, **{"Content-Type": "application/json"}),
		)
		if response.status_code != 200:
			error_message = response.json().get("error", {}).get("message", response.text)
			frappe.throw(_("Failed to publish flow: {0}").format(error_message))

		flow.status = "Published"
		flow.save()
		frappe.msgprint(_("Flow published successfully"))
	except Exception as e:
		frappe.throw(_("Failed to publish flow: {0}").format(str(e)))


def deprecate_flow(flow):
	"""
	Deprecate a published flow so it can't be sent any more.

	Parameters:
		flow (Document, required): WhatsApp Flow.

	Returns:
		None
	"""
	require_flow_id(flow)
	account, headers = get_flow_api(flow.whatsapp_account)
	try:
		make_post_request(
			get_graph_url(account, f"{flow.flow_id}/deprecate"),
			headers=dict(headers, **{"Content-Type": "application/json"}),
		)
		flow.status = "Deprecated"
		flow.save()
		frappe.msgprint(_("Flow deprecated successfully"))
	except Exception as e:
		frappe.throw(_("Failed to deprecate flow: {0}").format(str(e)))


def delete_flow_on_meta(flow):
	"""
	Delete a draft flow on WhatsApp and turn the local one back into a draft.

	Parameters:
		flow (Document, required): WhatsApp Flow.

	Returns:
		None
	"""
	if not flow.flow_id:
		frappe.throw(_("Flow does not exist on WhatsApp"))

	account, headers = get_flow_api(flow.whatsapp_account)
	try:
		response = requests.delete(get_graph_url(account, flow.flow_id), headers=headers)
		response.raise_for_status()

		flow.flow_id = None
		flow.status = "Draft"
		flow.save()
		frappe.msgprint(_("Flow deleted from WhatsApp"))
	except Exception as e:
		frappe.throw(_("Failed to delete flow: {0}").format(str(e)))


def send_test_flow(flow, phone_number, message=None):
	"""
	Send the flow to a phone number to try it (draft flows only reach test numbers).

	Parameters:
		flow (Document, required): WhatsApp Flow.
		phone_number (str, required): Recipient number.
		message (str, optional): Message text shown above the button.

	Returns:
		str: Name of the WhatsApp Message created.
	"""
	require_flow_id(flow)
	test_message = frappe.get_doc(
		{
			"doctype": "WhatsApp Message",
			"type": "Outgoing",
			"to": phone_number,
			"content_type": "flow",
			"flow": flow.name,
			"flow_cta": flow.flow_cta or "Open Form",
			"message": message or f"Test: {flow.flow_name}",
			"whatsapp_account": flow.whatsapp_account,
		}
	)
	test_message.insert(ignore_permissions=True)

	frappe.msgprint(_("Test flow sent to {0}").format(phone_number), indicator="green")
	return test_message.name


def require_flow_id(flow):
	"""
	Stop when the flow hasn't been created on WhatsApp yet.

	Parameters:
		flow (Document, required): WhatsApp Flow.

	Returns:
		None
	"""
	if not flow.flow_id:
		frappe.throw(_("Flow must be created on WhatsApp first"))
