# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Scheduler and background job entry points (see hooks.py)."""

import frappe

from frappe_whatsapp.frappe_whatsapp.doctype.bulk_whatsapp_message.bulk_status import update_queued_bulk_statuses
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_schedule import (
	send_payload_to_numbers,
)


def send_all_frequency_notifications():
	"""
	Scheduler "all": send notifications set to run every few minutes.

	Returns:
		None
	"""
	send_scheduled_notifications("All")


def send_hourly_notifications():
	"""
	Scheduler "hourly": send hourly notifications.

	Returns:
		None
	"""
	send_scheduled_notifications("Hourly")


def send_hourly_long_notifications():
	"""
	Scheduler "hourly_long": send long-running hourly notifications.

	Returns:
		None
	"""
	send_scheduled_notifications("Hourly Long")


def send_daily_notifications():
	"""
	Scheduler "daily": send daily notifications.

	Returns:
		None
	"""
	send_scheduled_notifications("Daily")


def send_daily_long_notifications():
	"""
	Scheduler "daily_long": send long-running daily notifications.

	Returns:
		None
	"""
	send_scheduled_notifications("Daily Long")


def send_weekly_notifications():
	"""
	Scheduler "weekly": send weekly notifications.

	Returns:
		None
	"""
	send_scheduled_notifications("Weekly")


def send_weekly_long_notifications():
	"""
	Scheduler "weekly_long": send long-running weekly notifications.

	Returns:
		None
	"""
	send_scheduled_notifications("Weekly Long")


def send_monthly_notifications():
	"""
	Scheduler "monthly": send monthly notifications.

	Returns:
		None
	"""
	send_scheduled_notifications("Monthly")


def send_monthly_long_notifications():
	"""
	Scheduler "monthly_long": send long-running monthly notifications.

	Returns:
		None
	"""
	send_scheduled_notifications("Monthly Long")


def send_scheduled_notifications(event_frequency):
	"""
	Send every enabled WhatsApp Notification set to this frequency.

	Parameters:
		event_frequency (str, required): e.g. "Hourly", "Daily Long".

	Returns:
		None
	"""
	notifications = frappe.get_list(
		"WhatsApp Notification",
		filters={"event_frequency": event_frequency, "disabled": 0},
	)
	for notification in notifications:
		frappe.get_doc("WhatsApp Notification", notification.name).send_scheduled_message()


def send_date_based_notifications(method="daily"):
	"""
	Scheduler "daily": send "Days Before" / "Days After" notifications due today.

	Parameters:
		method (str, optional): Only "daily" sends anything; kept for callers that pass it.

	Returns:
		None
	"""
	if frappe.flags.in_import or frappe.flags.in_patch:
		# Don't send notifications while syncing or patching.
		return

	if method != "daily":
		return

	notifications = frappe.get_all(
		"WhatsApp Notification",
		filters={"doctype_event": ("in", ("Days Before", "Days After")), "disabled": 0},
	)
	for notification in notifications:
		frappe.get_doc("WhatsApp Notification", notification.name).get_documents_for_today()


def send_role_notifications(
	notification, data, numbers, reference_doctype=None, reference_name=None, content_type=None
):
	"""
	Background job: send an already-built payload to role-based recipients.

	A role can resolve to dozens of people and Meta rate-limits per phone
	number id, so this runs on the long queue instead of in the request.

	Parameters:
		notification (str, required): WhatsApp Notification name.
		data (dict, required): Template payload; only "to" changes per recipient.
		numbers (list, required): Normalized phone numbers.
		reference_doctype (str, optional): DocType the notification is about.
		reference_name (str, optional): Document the notification is about.
		content_type (str, optional): Header type to log on the WhatsApp Message.

	Returns:
		None
	"""
	send_payload_to_numbers(
		notification, data, numbers, reference_doctype, reference_name, content_type
	)


def update_bulk_message_statuses():
	"""
	Mark queued Bulk WhatsApp Messages as Completed or Partially Failed once done.

	Returns:
		None
	"""
	update_queued_bulk_statuses()
