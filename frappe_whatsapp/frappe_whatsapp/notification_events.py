# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""
Send DocType Event WhatsApp Notifications.

hooks.py wires run_notifications_for_doc_event to every DocType ("*"), so
this has to stay cheap for documents nobody listens to: the map of which
notifications watch which DocType and event is cached.
"""

import frappe
from frappe.core.doctype.server_script.server_script_utils import EVENT_MAP

NOTIFICATION_MAP_CACHE_KEY = "whatsapp_notification_map"


def run_notifications_for_doc_event(doc, event):
	"""
	doc_events hook for every DocType: send the notifications set up for this event.

	Parameters:
		doc (Document, required): The document that fired the event.
		event (str, required): Hook name, e.g. "on_update".

	Returns:
		None
	"""
	if event not in EVENT_MAP:
		return

	if frappe.flags.in_install or frappe.flags.in_migrate or frappe.flags.in_uninstall:
		return

	notification_names = get_notifications_map().get(doc.doctype, {}).get(EVENT_MAP[event])
	if not notification_names:
		return

	for notification_name in notification_names:
		schedule_notification(notification_name, doc)


def schedule_notification(notification_name, doc):
	"""
	Send a notification once the current transaction has committed.

	Frappe v16 doesn't allow frappe.db.commit() inside doc hooks, so the
	Meta call waits until after commit. That also makes sure share keys for
	print attachments are saved before Meta tries to open the link.
	Frappe v14/v15 have no after_commit, so there it sends straight away.

	Parameters:
		notification_name (str, required): WhatsApp Notification to send.
		doc (Document, required): Document the notification is about.

	Returns:
		None
	"""
	if hasattr(frappe.db, "after_commit"):
		frappe.db.after_commit.add(
			lambda: send_notification(notification_name, doc.doctype, doc.name, commit=True)
		)
	else:
		send_notification(notification_name, doc.doctype, doc.name)


def send_notification(notification_name, doctype, docname, commit=False):
	"""
	Load the document fresh and send one WhatsApp Notification for it.

	Parameters:
		notification_name (str, required): WhatsApp Notification to send.
		doctype (str, required): Reference DocType.
		docname (str, required): Reference document name.
		commit (bool, optional): Commit our own writes; set when running after commit,
			outside the request's auto-commit.

	Returns:
		None
	"""
	try:
		doc = frappe.get_doc(doctype, docname)
		frappe.get_doc("WhatsApp Notification", notification_name).send_template_message(doc)
		if commit:
			# nosemgrep: frappe-manual-commit -- runs in after_commit callback outside request scope; WhatsApp Message + Notification Log rows rely on this to persist
			frappe.db.commit()
	except Exception:
		if commit:
			frappe.db.rollback()
		frappe.log_error(title=f"WhatsApp Notification failed: {notification_name}")


def get_notifications_map():
	"""
	Which enabled DocType Event notifications watch which DocType and event.

	Returns:
		dict: {reference_doctype: {doctype_event: [notification names]}},
		e.g. {"Sales Invoice": {"on_submit": ["Invoice Alert"]}}.
	"""
	cached_map = frappe.cache().get_value(NOTIFICATION_MAP_CACHE_KEY)
	if cached_map:
		return cached_map

	if frappe.flags.in_patch and not frappe.db.table_exists("WhatsApp Notification"):
		return {}

	notification_map = {}
	notifications = frappe.get_all(
		"WhatsApp Notification",
		fields=("name", "reference_doctype", "doctype_event", "notification_type"),
		filters={"disabled": 0},
	)
	for notification in notifications:
		if notification.notification_type != "DocType Event":
			continue

		events = notification_map.setdefault(notification.reference_doctype, {})
		events.setdefault(notification.doctype_event, []).append(notification.name)

	frappe.cache().set_value(NOTIFICATION_MAP_CACHE_KEY, notification_map)

	return notification_map


def clear_notifications_map():
	"""
	Forget the cached notification map so it is rebuilt on the next event.

	Returns:
		None
	"""
	frappe.cache().delete_value(NOTIFICATION_MAP_CACHE_KEY)
