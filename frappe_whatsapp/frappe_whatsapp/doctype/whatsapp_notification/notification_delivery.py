# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Post a notification message to Meta, save it as a WhatsApp Message, and log the result."""

import frappe
from frappe import _

from frappe_whatsapp.utils.meta_api import get_meta_error, get_meta_response, get_whatsapp_account, post_message


def send_and_log(notification, data, doc_data=None):
	"""
	Post one template message, save it as a WhatsApp Message and log Meta's answer.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		data (dict, required): Payload with "to" set.
		doc_data (dict, optional): Reference document, linked on the WhatsApp Message.

	Returns:
		bool: True when Meta accepted the message.
	"""
	if notification.whatsapp_account:
		account = frappe.get_doc("WhatsApp Account", notification.whatsapp_account)
	else:
		account = get_whatsapp_account(account_type="outgoing")
	if not account:
		frappe.throw(_("Please set a default outgoing WhatsApp Account"))

	success = False
	error_message = None
	try:
		response = post_message(account, data)
		save_sent_message(notification, data, response, account.name, doc_data)
		success = True
	except Exception as e:
		error = get_meta_error()
		error_message = error.get("Error", error.get("message")) or str(e)
		frappe.msgprint(f"Failed to trigger whatsapp message: {error_message}", indicator="red", alert=True)
	finally:
		meta_data = get_meta_response() if success else {"error": error_message}
		frappe.get_doc(
			{"doctype": "WhatsApp Notification Log", "template": notification.template, "meta_data": meta_data}
		).insert(ignore_permissions=True)

	return success


def save_sent_message(notification, data, response, account_name, doc_data=None):
	"""
	Record a sent template as an Outgoing WhatsApp Message.

	It already has Meta's message id, so WhatsApp Message won't send it again.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		data (dict, required): The payload that was sent.
		response (dict, required): Meta's response.
		account_name (str, required): WhatsApp Account it was sent from.
		doc_data (dict, optional): Reference document.

	Returns:
		None
	"""
	if not notification.get("content_type"):
		notification.content_type = "text"

	parameters = None
	components = data["template"]["components"]
	if components:
		values = [parameter["text"] for parameter in components[0]["parameters"]]
		parameters = frappe.json.dumps(values, default=str)

	message = {
		"doctype": "WhatsApp Message",
		"type": "Outgoing",
		"message": str(data["template"]),
		"to": data["to"],
		"message_type": "Template",
		"message_id": response["messages"][0]["id"],
		"content_type": notification.content_type,
		"use_template": 1,
		"template": notification.template,
		"template_parameters": parameters,
		"whatsapp_account": account_name,
	}
	if doc_data:
		message["reference_doctype"] = doc_data.doctype
		message["reference_name"] = doc_data.name

	frappe.get_doc(message).save(ignore_permissions=True)


def apply_property_after_alert(notification, doc_data):
	"""
	Set the configured field on the reference document after a successful send.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		doc_data (dict, required): Reference document with doctype and name.

	Returns:
		None
	"""
	if not (doc_data and notification.set_property_after_alert and notification.property_value):
		return

	if not (doc_data.get("doctype") and doc_data.get("name")):
		return

	fieldname = notification.set_property_after_alert
	field = frappe.get_meta(doc_data.get("doctype")).get_field(fieldname)
	if not field:
		return

	value = notification.property_value
	if field.fieldtype in frappe.model.numeric_fieldtypes:
		value = frappe.utils.cint(value)

	frappe.db.set_value(doc_data.get("doctype"), doc_data.get("name"), fieldname, value)
