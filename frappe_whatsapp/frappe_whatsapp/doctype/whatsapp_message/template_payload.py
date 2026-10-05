# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Build the Meta payload for a template WhatsApp Message."""

import json

import frappe

from frappe_whatsapp.utils.phone import format_number


def build_template_payload(doc):
	"""
	Build the request body for sending an approved template.

	Also stores the filled-in values on doc.template_parameters.

	Parameters:
		doc (Document, required): Outgoing WhatsApp Message with "template" set.

	Returns:
		dict: Payload for Meta's /messages endpoint.
	"""
	template = frappe.get_doc("WhatsApp Templates", doc.template)
	components = []

	parameters = get_body_parameters(doc, template)
	# Meta expects the body component even when it has no parameters.
	components.append({"type": "body", "parameters": parameters})

	header = build_header(doc, template)
	if header:
		components.append(header)

	mpm_button = build_mpm_button(doc)
	if mpm_button:
		components.append(mpm_button)

	components.extend(build_button_parameters(doc, template, has_mpm=bool(mpm_button)))

	return {
		"messaging_product": "whatsapp",
		"to": format_number(doc.to),
		"type": "template",
		"template": {
			"name": template.actual_name or template.template_name,
			"language": {"code": template.language_code},
			"components": components,
		},
	}


def get_body_parameters(doc, template):
	"""
	Values for the template's {{1}}, {{2}}... placeholders.

	They come from, in order of preference: body_param (JSON set by bulk
	messages), flags.custom_ref_doc (recipient data), or the fields named in
	the template read from the reference document.

	Parameters:
		doc (Document, required): WhatsApp Message being sent.
		template (Document, required): Its WhatsApp Template.

	Returns:
		list: Body parameters, e.g. [{"type": "text", "text": "INV-0001"}].
	"""
	if not template.sample_values:
		return []

	if template.field_names:
		field_names = template.field_names.split(",")
	else:
		field_names = template.sample_values.split(",")

	values = []
	if doc.body_param is not None:
		values = list(json.loads(doc.body_param).values())
	elif doc.flags.custom_ref_doc:
		for field_name in field_names:
			values.append(doc.flags.custom_ref_doc.get(field_name.strip()))
	else:
		reference_doc = frappe.get_doc(doc.reference_doctype, doc.reference_name)
		for field_name in field_names:
			values.append(reference_doc.get_formatted(field_name.strip()))

	doc.template_parameters = json.dumps(values)

	parameters = []
	for value in values:
		parameters.append({"type": "text", "text": value})

	return parameters


def build_header(doc, template):
	"""
	Image or document header, from the message's attachment or the template's sample image.

	Parameters:
		doc (Document, required): WhatsApp Message being sent.
		template (Document, required): Its WhatsApp Template.

	Returns:
		dict | None: Header component, or None when the template needs none.
	"""
	if not template.header_type:
		return None

	if doc.attach:
		url = get_full_url(doc.attach)
		if template.header_type == "IMAGE":
			return {"type": "header", "parameters": [{"type": "image", "image": {"link": url}}]}
		if template.header_type == "DOCUMENT":
			# The filename shown to the customer isn't configurable yet.
			document = {"link": url, "filename": "document.pdf"}
			return {"type": "header", "parameters": [{"type": "document", "document": document}]}
		return None

	if template.sample and template.header_type == "IMAGE":
		url = get_full_url(template.sample)
		return {"type": "header", "parameters": [{"type": "image", "image": {"link": url}}]}

	return None


def build_mpm_button(doc):
	"""
	Multi-Product Message button from product_catalog_json, if the message has one.

	Parameters:
		doc (Document, required): WhatsApp Message being sent.

	Returns:
		dict | None: The MPM button component, always at index 0.
	"""
	if not doc.product_catalog_json:
		return None

	try:
		catalog_action = json.loads(doc.product_catalog_json)
	except Exception as e:
		frappe.log_error(f"Failed to parse Product Catalog JSON: {str(e)}", "WhatsApp MPM Error")
		return None

	return {
		"type": "button",
		"sub_type": "mpm",
		"index": "0",
		"parameters": [{"type": "action", "action": catalog_action}],
	}


def build_button_parameters(doc, template, has_mpm=False):
	"""
	Button components for buttons whose value is filled in at send time.

	Static "Call Phone" and static "Visit Website" buttons are left out: Meta
	applies them from the approved template and rejects them here
	("sub_type must be one of ...", see upstream issue #188).

	Parameters:
		doc (Document, required): WhatsApp Message being sent.
		template (Document, required): Its WhatsApp Template.
		has_mpm (bool, optional): An MPM button took index 0, so the others shift by one.

	Returns:
		list: Button components.
	"""
	components = []
	for idx, button in enumerate(template.buttons or []):
		index = str(idx + 1) if has_mpm else str(idx)

		if button.button_type == "Quick Reply":
			components.append(
				{
					"type": "button",
					"sub_type": "quick_reply",
					"index": index,
					"parameters": [{"type": "payload", "payload": button.button_label}],
				}
			)
		elif button.button_type == "Visit Website" and button.url_type == "Dynamic":
			reference_doc = frappe.get_doc(doc.reference_doctype, doc.reference_name)
			url = reference_doc.get_formatted(button.website_url)
			components.append(
				{
					"type": "button",
					"sub_type": "url",
					"index": index,
					"parameters": [{"type": "text", "text": url}],
				}
			)

	return components


def get_full_url(path):
	"""
	Turn a site path like "/files/a.png" into a full URL; full URLs are returned as they are.

	Parameters:
		path (str, required): File path or URL.

	Returns:
		str: Full URL.
	"""
	if path.startswith("http"):
		return path

	return f"{frappe.utils.get_url()}{path}"
