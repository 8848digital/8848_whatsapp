# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Work out who a WhatsApp Notification goes to for one document, and send it."""

import frappe
from frappe.utils.safe_exec import get_safe_globals

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_payload import (
	build_notification_payload,
)
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_recipients import (
	get_role_recipients,
	log_skipped,
)
from frappe_whatsapp.utils.phone import format_number

ROLE_JOB = "frappe_whatsapp.frappe_whatsapp.tasks.send_role_notifications"


def send_for_document(notification, doc, phone_no=None, default_template=None, ignore_condition=False):
	"""
	Send the notification's template about one document.

	Field-based numbers are sent straight away; role-based numbers go to a
	background job, because a role can mean dozens of people.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		doc (Document, required): The reference document.
		phone_no (str, optional): Send only to this number.
		default_template (Document | dict, optional): Template to use instead of the notification's.
		ignore_condition (bool, optional): Skip the notification's condition.

	Returns:
		None
	"""
	if notification.disabled:
		return

	doc_data = doc.as_dict()
	if notification.condition and not ignore_condition:
		if not frappe.safe_eval(notification.condition, get_safe_globals(), dict(doc=doc_data)):
			return

	template = default_template or frappe.get_doc("WhatsApp Templates", notification.template)
	if not template:
		return

	inline_numbers, role_numbers = notification.get_recipients(doc, doc_data, phone_no)
	if not inline_numbers and not role_numbers:
		return

	data = build_notification_payload(notification, doc, doc_data, template)

	sent = 0
	for number in inline_numbers:
		data["to"] = number
		if notification.notify(data, doc_data):
			sent += 1

	if role_numbers:
		frappe.enqueue(
			ROLE_JOB,
			queue="long",
			enqueue_after_commit=True,
			notification=notification.name,
			data=dict(data, to=None),
			numbers=role_numbers,
			reference_doctype=doc_data.get("doctype"),
			reference_name=doc_data.get("name"),
			content_type=notification.get("content_type"),
		)

	if sent:
		try:
			notification.apply_property_after_alert(doc_data)
		except Exception:
			frappe.log_error(title=f"WhatsApp Notification: apply_property_after_alert failed: {notification.name}")

		message = "WhatsApp Message Triggered" if sent == 1 else f"WhatsApp Message Triggered for {sent} recipients"
		frappe.msgprint(message, indicator="green", alert=True)
	elif role_numbers:
		frappe.msgprint(f"WhatsApp message queued for {len(role_numbers)} recipients", indicator="green", alert=True)


def get_recipients(notification, doc, doc_data, phone_no=None):
	"""
	Numbers to send to, split into (inline_numbers, role_numbers).

	An explicit phone_no is the only recipient: the _data_list scheduler path
	lists its own recipient per row, so adding roles there would send the
	same message once per row.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		doc (Document, required): The reference document.
		doc_data (dict, required): doc.as_dict().
		phone_no (str, optional): Explicit recipient.

	Returns:
		tuple: (list of numbers sent inline, list of numbers for the role job)
	"""
	if phone_no:
		return [format_number(phone_no)], []

	inline_numbers = []
	if notification.field_name and doc_data.get(notification.field_name):
		inline_numbers.append(format_number(doc_data.get(notification.field_name)))

	role_numbers = []
	if notification.get("recipients"):
		role_recipients, skipped = get_role_recipients(notification, doc)
		log_skipped(notification.name, skipped)
		for recipient in role_recipients:
			role_numbers.append(recipient["phone"])

	inline_numbers = remove_duplicates(inline_numbers)
	# Someone already messaged inline must not get the role message too.
	role_numbers = [number for number in remove_duplicates(role_numbers) if number not in inline_numbers]

	return inline_numbers, role_numbers


def remove_duplicates(numbers):
	"""
	Drop blanks and repeats, keeping the original order.

	Parameters:
		numbers (list, required): Phone numbers.

	Returns:
		list: Unique, non-empty numbers.
	"""
	unique_numbers = []
	for number in numbers:
		if number and number not in unique_numbers:
			unique_numbers.append(number)

	return unique_numbers
