# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Scheduled, date-based and background (role) sends of WhatsApp Notifications."""

import frappe
from frappe.utils import add_to_date, nowdate
from frappe.utils.safe_exec import get_safe_globals, safe_exec

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_recipients import (
	get_role_recipients,
	log_skipped,
)
from frappe_whatsapp.utils.phone import format_number


def send_scheduled(notification):
	"""
	Send a Scheduler Event notification.

	A server-script condition can fill notification._contact_list (numbers,
	no document) or notification._data_list ([{"name", "phone_no"}] rows of
	the reference DocType). Without either, role recipients get a
	parameter-less template.

	Parameters:
		notification (Document, required): The WhatsApp Notification.

	Returns:
		None
	"""
	if notification.condition:
		# nosemgrep: frappe-codeinjection-eval -- safe_exec is Frappe's sandboxed eval; condition is admin-write-gated
		safe_exec(notification.condition, get_safe_globals(), dict(doc=notification))

	template = frappe.db.get_value("WhatsApp Templates", notification.template, fieldname="*")
	if not template or not template.language_code:
		return

	if notification.get("_contact_list"):
		notification.send_simple_template(template)
	elif notification.get("_data_list"):
		for row in notification._data_list:
			doc = frappe.get_doc(notification.reference_doctype, row.get("name"))
			notification.send_template_message(doc, row.get("phone_no"), template, True)
	elif notification.notification_type == "Scheduler Event" and notification.get("recipients"):
		# The notification_type check matters: the scheduler picks notifications
		# by event_frequency alone, and DocType Event ones still carry the hidden
		# default "All", which would send them here every few minutes.
		role_recipients, skipped = get_role_recipients(notification, doc=None)
		log_skipped(notification.name, skipped)
		notification._contact_list = [recipient["phone"] for recipient in role_recipients]
		if notification._contact_list:
			notification.send_simple_template(template)


def send_without_document(notification, template):
	"""
	Send a template with no parameters to every number in notification._contact_list.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		template (dict, required): WhatsApp Templates row.

	Returns:
		None
	"""
	for contact in notification._contact_list:
		data = {
			"messaging_product": "whatsapp",
			"to": format_number(contact) if contact else contact,
			"type": "template",
			"template": {
				"name": template.actual_name,
				"language": {"code": template.language_code},
				"components": [],
			},
		}
		notification.content_type = (template.get("header_type") or "text").lower()
		notification.notify(data)


def send_for_documents_due_today(notification):
	"""
	Send a "Days Before" / "Days After" notification for documents whose date is today ± the offset.

	Parameters:
		notification (Document, required): The WhatsApp Notification.

	Returns:
		None
	"""
	offset_days = notification.days_in_advance
	if notification.doctype_event == "Days After":
		offset_days = -offset_days

	reference_date = add_to_date(nowdate(), days=offset_days)
	documents = frappe.get_all(
		notification.reference_doctype,
		fields="name",
		filters=[
			{notification.date_changed: (">=", reference_date + " 00:00:00.000000")},
			{notification.date_changed: ("<=", reference_date + " 23:59:59.000000")},
		],
	)
	for document in documents:
		notification.send_template_message(frappe.get_doc(notification.reference_doctype, document.name))


def send_payload_to_numbers(notification_name, data, numbers, reference_doctype=None, reference_name=None, content_type=None):
	"""
	Background job body: send one built payload to many role-based numbers.

	Parameters:
		notification_name (str, required): WhatsApp Notification name.
		data (dict, required): Payload; only "to" changes per number.
		numbers (list, required): Normalized phone numbers.
		reference_doctype (str, optional): DocType the notification is about.
		reference_name (str, optional): Document the notification is about.
		content_type (str, optional): Header type to log (it isn't saved on the notification).

	Returns:
		None
	"""
	try:
		notification = frappe.get_doc("WhatsApp Notification", notification_name)
	except Exception:
		frappe.log_error(title=f"WhatsApp role notification: notification not found: {notification_name}")
		return

	if content_type:
		notification.content_type = content_type

	# notify only needs doctype and name, so no need to load the document.
	doc_data = None
	if reference_doctype and reference_name:
		doc_data = frappe._dict(doctype=reference_doctype, name=reference_name)

	sent = 0
	for number in numbers:
		data["to"] = number
		try:
			if notification.notify(data, doc_data):
				sent += 1
		except Exception:
			# One bad number must not stop the rest of the batch.
			frappe.log_error(
				title=f"WhatsApp role notification failed: {notification_name}",
				message=f"Recipient: {number}\n\n{frappe.get_traceback()}",
			)

	if sent and doc_data:
		notification.apply_property_after_alert(doc_data)
