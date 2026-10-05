# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Build the template payload a WhatsApp Notification sends for a document."""

import datetime
from urllib.parse import quote

import frappe
from frappe.desk.form.utils import get_pdf_link
from frappe.model.document import Document

from frappe_whatsapp.utils.template_params import sanitize_param


def build_notification_payload(notification, doc, doc_data, template):
	"""
	Template payload for one document; "to" is left empty and set per recipient.

	Also sets notification.content_type from the template's header, which
	is logged on the WhatsApp Message.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		doc (Document | dict, required): The reference document.
		doc_data (dict, required): doc.as_dict().
		template (Document | dict, required): The WhatsApp Template to send.

	Returns:
		dict: Payload for Meta's /messages endpoint.
	"""
	components = []
	if notification.fields:
		components = [{"type": "body", "parameters": get_body_parameters(notification, doc, doc_data)}]

	header = build_attachment_header(notification, doc, doc_data, template)
	if header:
		components.append(header)

	notification.content_type = template.header_type.lower() if template.header_type else None

	components.extend(build_buttons(notification, doc, template, components))

	return {
		"messaging_product": "whatsapp",
		"to": None,
		"type": "template",
		"template": {
			"name": template.actual_name,
			"language": {"code": template.language_code},
			"components": components,
		},
	}


def get_body_parameters(notification, doc, doc_data):
	"""
	Body parameters from the notification's mapped fields, in order.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		doc (Document | dict, required): The reference document.
		doc_data (dict, required): doc.as_dict().

	Returns:
		list: e.g. [{"type": "text", "text": "SINV-0001"}].
	"""
	parameters = []
	for field in notification.fields:
		if isinstance(doc, Document):
			# get_formatted gives the value as users see it, e.g. "₹ 1,000.00".
			value = doc.get_formatted(field.field_name)
		else:
			value = doc_data[field.field_name]
			if isinstance(value, (datetime.date, datetime.datetime)):
				value = str(value)

		if notification.get("recipients"):
			# Role notifications often map Text Editor fields, whose HTML Meta
			# would show as plain text. Only this path is cleaned, so existing
			# field-based notifications send exactly as before.
			value = sanitize_param(value)

		parameters.append({"type": "text", "text": value})

	return parameters


def build_attachment_header(notification, doc, doc_data, template):
	"""
	Document or image header with the document's print, or a custom attachment.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		doc (Document, required): The reference document.
		doc_data (dict, required): doc.as_dict().
		template (Document | dict, required): The WhatsApp Template.

	Returns:
		dict | None: Header component, or None when there is nothing to attach.
	"""
	if template.header_type not in ("DOCUMENT", "IMAGE"):
		return None

	url, filename = get_attachment(notification, doc, doc_data)
	if not url:
		return None

	if template.header_type == "DOCUMENT":
		document = {"link": url, "filename": filename}
		return {"type": "header", "parameters": [{"type": "document", "document": document}]}

	return {"type": "header", "parameters": [{"type": "image", "image": {"link": url}}]}


def get_attachment(notification, doc, doc_data):
	"""
	Public URL and file name of what the notification attaches.

	Private files and prints get a document share key in the URL so Meta can download them.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		doc (Document, required): The reference document.
		doc_data (dict, required): doc.as_dict().

	Returns:
		tuple: (url or None, filename or None)
	"""
	if notification.attach_document_print:
		key = doc.get_document_share_key()
		link = get_pdf_link(doc_data["doctype"], doc_data["name"], print_format=get_print_format(doc_data["doctype"]))
		return f"{frappe.utils.get_url()}{link}&key={key}", f'{doc_data["name"]}.pdf'

	if not notification.custom_attachment:
		return None, None

	if notification.attach_from_field:
		file_url = doc_data[notification.attach_from_field]
		if not file_url.startswith("http"):
			key = doc.get_document_share_key()
			# Quoted so file names with spaces or brackets still download.
			file_url = f"{frappe.utils.get_url()}{quote(file_url)}?key={key}"
	else:
		file_url = notification.attach

	if not file_url.startswith("http"):
		file_url = f"{frappe.utils.get_url()}{file_url}"

	return file_url, notification.file_name


def get_print_format(doctype):
	"""
	The DocType's default print format, or "Standard".

	Parameters:
		doctype (str, required): DocType being printed.

	Returns:
		str: Print format name.
	"""
	doctype_doc = frappe.get_doc("DocType", doctype)
	if doctype_doc.custom:
		return doctype_doc.default_print_format or "Standard"

	default_print_format = frappe.db.get_value(
		"Property Setter", filters={"doc_type": doctype, "property": "default_print_format"}, fieldname="value"
	)
	return default_print_format or "Standard"


def build_buttons(notification, doc, template, components):
	"""
	Button components whose values come from the document.

	"Button Fields" lists the document fields to use, in the order of the
	template's dynamic buttons. An OTP copy-code button reuses the first body
	parameter as the code.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		doc (Document, required): The reference document.
		template (Document | dict, required): The WhatsApp Template.
		components (list, required): Components built so far (to read the body).

	Returns:
		list: Button components.
	"""
	if not template.buttons:
		return []

	button_fields = notification.button_fields.split(",") if notification.button_fields else []
	buttons = []
	for idx, button in enumerate(template.buttons):
		index = str(idx)
		if button.button_type == "Visit Website" and "otp_type=COPY_CODE" in (button.website_url or ""):
			otp_code = get_first_body_value(components)
			if otp_code:
				buttons.append(button_component("url", index, {"type": "text", "text": str(otp_code)}))
		elif not button_fields:
			continue
		elif button.button_type == "Visit Website" and button.url_type == "Dynamic":
			buttons.append(button_component("url", index, {"type": "text", "text": doc.get(button_fields.pop(0))}))
		elif button.button_type == "Multi-Product Message":
			buttons.append(button_component("mpm", index, {"type": "action", "action": doc.get(button_fields.pop(0))}))
		elif button.button_type == "Catalog":
			buttons.append(button_component("catalog", index, {"type": "action", "action": doc.get(button_fields.pop(0))}))

	return buttons


def get_first_body_value(components):
	"""
	Text of the first body parameter, used as the OTP code.

	Parameters:
		components (list, required): Template components.

	Returns:
		str | None: The value, or None when the body has no parameters.
	"""
	for component in components:
		if component.get("type") != "body":
			continue
		if component.get("parameters"):
			return component["parameters"][0].get("text")
		return None

	return None


def button_component(sub_type, index, parameter):
	"""
	One button component in Meta's format.

	Parameters:
		sub_type (str, required): "url", "mpm" or "catalog".
		index (str, required): Button position in the template, as a string.
		parameter (dict, required): The button's single parameter.

	Returns:
		dict: Button component.
	"""
	return {"type": "button", "sub_type": sub_type, "index": index, "parameters": [parameter]}
