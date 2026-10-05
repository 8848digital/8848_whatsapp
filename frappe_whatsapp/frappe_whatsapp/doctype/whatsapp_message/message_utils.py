# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Sending, read receipts and sender profiles for WhatsApp Message."""

import frappe
from frappe import _

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message.message_payload import build_outgoing_payload
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message.template_payload import build_template_payload
from frappe_whatsapp.utils.meta_api import (
	get_meta_error,
	get_meta_response,
	get_whatsapp_account,
	post_message,
)
from frappe_whatsapp.utils.phone import format_number


def set_default_account(doc):
	"""
	Fill in the default incoming/outgoing WhatsApp Account when none is chosen.

	Parameters:
		doc (Document, required): WhatsApp Message.

	Returns:
		None
	"""
	if doc.whatsapp_account:
		return

	account_type = "outgoing" if doc.type == "Outgoing" else "incoming"
	default_account = get_whatsapp_account(account_type=account_type)
	if not default_account:
		frappe.throw(_("Please set a default outgoing WhatsApp Account or Select available WhatsApp Account"))

	doc.whatsapp_account = default_account.name


def send_outgoing(doc):
	"""
	Send an Outgoing message to Meta; does nothing for incoming messages.

	Called before insert for new messages and by bulk retry for Failed ones.
	Non-template sends set the status and raise on failure; template sends
	raise from send_payload.

	Parameters:
		doc (Document, required): WhatsApp Message.

	Returns:
		None
	"""
	if doc.type != "Outgoing":
		return

	if doc.message_type == "Template":
		if not doc.message_id:
			send_template(doc)
		return

	data = build_outgoing_payload(doc)
	try:
		send_payload(doc, data)
		doc.status = "Success"
	except Exception as e:
		doc.status = "Failed"
		frappe.throw(f"Failed to send message {str(e)}")


def send_template(doc):
	"""
	Send the message's WhatsApp Template.

	Parameters:
		doc (Document, required): WhatsApp Message with "template" set.

	Returns:
		None
	"""
	send_payload(doc, build_template_payload(doc))


def send_payload(doc, data):
	"""
	Post a payload to Meta and store the returned message id on the document.

	On failure Meta's answer is logged to WhatsApp Notification Log and its
	message shown to the user.

	Parameters:
		doc (Document, required): WhatsApp Message being sent.
		data (dict, required): Meta payload.

	Returns:
		None
	"""
	account = frappe.get_doc("WhatsApp Account", doc.whatsapp_account)
	try:
		response = post_message(account, data)
		doc.message_id = response["messages"][0]["id"]
	except Exception as e:
		error = get_meta_error()
		frappe.get_doc(
			{"doctype": "WhatsApp Notification Log", "template": "Text Message", "meta_data": get_meta_response()}
		).insert(ignore_permissions=True)

		frappe.throw(msg=error.get("Error", error.get("message")) or str(e), title=error.get("error_user_title", "Error"))


def send_read_receipt(doc):
	"""
	Tell Meta the incoming message was read (blue ticks) and mark it so here.

	Parameters:
		doc (Document, required): Incoming WhatsApp Message.

	Returns:
		bool | None: True when Meta accepted it, None on failure (the error is logged).
	"""
	account = frappe.get_doc("WhatsApp Account", doc.whatsapp_account)
	data = {"messaging_product": "whatsapp", "status": "read", "message_id": doc.message_id}

	try:
		response = post_message(account, data)
	except Exception:
		error = get_meta_error()
		frappe.log_error("WhatsApp API Error", f"{error.get('Error', error.get('message'))}\n{error}")
		return None

	if response.get("success"):
		doc.status = "marked as read"
		doc.save()
		return response.get("success")

	return None


def mark_message_as_read(message_name):
	"""
	Load a WhatsApp Message the user can read and send its read receipt.

	Parameters:
		message_name (str, required): WhatsApp Message name.

	Returns:
		bool | None: True when Meta accepted it.
	"""
	message_doc = frappe.get_doc("WhatsApp Message", message_name)
	message_doc.check_permission("read")

	return message_doc.send_read_receipt()


def create_profile(doc):
	"""
	Create a WhatsApp Profile for the other party's number if there isn't one.

	Parameters:
		doc (Document, required): WhatsApp Message.

	Returns:
		None
	"""
	number = format_number(doc.get("from") or doc.to)
	if frappe.db.exists("WhatsApp Profiles", {"number": number}):
		return

	frappe.get_doc(
		{
			"doctype": "WhatsApp Profiles",
			"profile_name": doc.profile_name,
			"number": number,
			"whatsapp_account": doc.whatsapp_account,
		}
	).insert(ignore_permissions=True)


def update_profile_name(doc):
	"""
	Copy a changed sender profile name onto their WhatsApp Profile.

	Parameters:
		doc (Document, required): Incoming WhatsApp Message.

	Returns:
		None
	"""
	if not doc.get("from") or not doc.profile_name or not doc.has_value_changed("profile_name"):
		return

	number = format_number(doc.get("from"))
	profile_name = frappe.db.get_value("WhatsApp Profiles", {"number": number}, "name")
	if profile_name:
		frappe.db.set_value("WhatsApp Profiles", profile_name, "profile_name", doc.profile_name)


def create_template_message(to, reference_doctype, reference_name, template):
	"""
	Create (and so send) a template message about a document.

	Parameters:
		to (str, required): Recipient's number.
		reference_doctype (str, required): DocType the message is about.
		reference_name (str, required): Document the message is about.
		template (str, required): WhatsApp Template name.

	Returns:
		Document: The saved WhatsApp Message.
	"""
	message = frappe.get_doc(
		{
			"doctype": "WhatsApp Message",
			"to": to,
			"type": "Outgoing",
			"message_type": "Template",
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"content_type": "text",
			"template": template,
		}
	)
	message.save()

	return message
