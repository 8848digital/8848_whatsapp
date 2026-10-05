# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Create, update and delete WhatsApp Templates on Meta."""

import json

import frappe
from frappe.integrations.utils import make_post_request, make_request

from frappe_whatsapp.utils.meta_api import get_auth_headers, get_graph_url, get_meta_error


def create_template_on_meta(template):
	"""
	Submit a new template to Meta for approval and store its id and status.

	Parameters:
		template (Document, required): WhatsApp Templates record just inserted.

	Returns:
		None
	"""
	if template.template_name:
		template.actual_name = template.template_name.lower().replace(" ", "_")

	account = frappe.get_doc("WhatsApp Account", template.whatsapp_account)
	data = {
		"name": template.actual_name,
		"language": template.language_code,
		"category": template.category,
		"components": build_components(template),
	}

	try:
		response = make_post_request(
			get_graph_url(account, f"{account.business_id}/message_templates"),
			headers=get_auth_headers(account),
			data=json.dumps(data),
		)
	except Exception:
		error = get_meta_error()
		frappe.throw(msg=error.get("error_user_msg", error.get("message")), title=error.get("error_user_title", "Error"))

	template.id = response["id"]
	template.status = response["status"]
	# Saved with db_update because this runs in after_insert, after the row exists.
	template.db_update()


def update_template_on_meta(template):
	"""
	Send the edited body, header, footer and buttons to Meta.

	Parameters:
		template (Document, required): WhatsApp Templates record being saved.

	Returns:
		None
	"""
	account = frappe.get_doc("WhatsApp Account", template.whatsapp_account)
	make_post_request(
		get_graph_url(account, template.id),
		headers=get_auth_headers(account),
		data=json.dumps({"components": build_components(template)}),
	)


def delete_template_on_meta(template):
	"""
	Delete the template on Meta. A template Meta no longer has is only deleted here.

	Parameters:
		template (Document, required): WhatsApp Templates record being deleted.

	Returns:
		None
	"""
	account = frappe.get_doc("WhatsApp Account", template.whatsapp_account)
	url = get_graph_url(account, f"{account.business_id}/message_templates?name={template.actual_name}")

	try:
		make_request("DELETE", url, headers=get_auth_headers(account))
	except Exception:
		error = get_meta_error()
		if error.get("error_user_title") == "Message Template Not Found":
			frappe.msgprint("Deleted locally", error.get("error_user_title", "Error"), alert=True)
		else:
			frappe.throw(msg=error.get("error_user_msg"), title=error.get("error_user_title", "Error"))


def build_components(template):
	"""
	Body, header, footer and buttons in Meta's template format.

	Parameters:
		template (Document, required): WhatsApp Templates record.

	Returns:
		list: Template components.
	"""
	body = {"type": "BODY", "text": template.template}
	if template.sample_values:
		body["example"] = {"body_text": [template.sample_values.split(",")]}

	components = [body]
	if template.header_type:
		components.append(build_header(template))

	if template.footer:
		components.append({"type": "FOOTER", "text": template.footer})

	if template.buttons:
		buttons = []
		for button in template.buttons:
			buttons.append(build_button(button))
		components.append({"type": "BUTTONS", "buttons": buttons})

	return components


def build_header(template):
	"""
	Header component: text with its samples, or the uploaded sample media handle.

	Parameters:
		template (Document, required): WhatsApp Templates record.

	Returns:
		dict: Header component.
	"""
	header = {"type": "header", "format": template.header_type}

	if template.header_type == "TEXT":
		header["text"] = template.header
		if template.sample:
			header["example"] = {"header_text": template.sample.split(", ")}
	else:
		header["example"] = {"header_handle": [template.flags.media_handle]}

	return header


def build_button(button):
	"""
	One button in Meta's format.

	An authentication copy-code button is stored locally as a "Visit Website"
	button whose URL contains otp_type=COPY_CODE; Meta wants it as type OTP.

	Parameters:
		button (Document, required): WhatsApp Button row.

	Returns:
		dict: Button definition, e.g. {"type": "QUICK_REPLY", "text": "Yes"}.
	"""
	if button.button_type == "Visit Website" and "otp_type=COPY_CODE" in (button.website_url or ""):
		return {"type": "OTP", "otp_type": "COPY_CODE"}

	meta_button = {"type": button.button_type, "text": button.button_label}

	if button.button_type == "Visit Website":
		meta_button["type"] = "URL"
		meta_button["url"] = button.website_url
		if button.url_type == "Dynamic" and button.example_url:
			meta_button["example"] = button.example_url.split(",")
	elif button.button_type == "Call Phone":
		meta_button["type"] = "PHONE_NUMBER"
		meta_button["phone_number"] = button.phone_number
	elif button.button_type == "Quick Reply":
		meta_button["type"] = "QUICK_REPLY"
	elif button.button_type == "Multi-Product Message":
		meta_button["type"] = "MPM"
	elif button.button_type == "Catalog":
		meta_button["type"] = "CATALOG"

	return meta_button
