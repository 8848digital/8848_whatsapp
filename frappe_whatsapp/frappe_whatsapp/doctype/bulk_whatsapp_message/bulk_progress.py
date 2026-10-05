# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Progress counts and retries for the messages of a Bulk WhatsApp Message."""

import frappe
from frappe import _


SENT_STATUSES = ["sent", "delivered", "Success", "read"]


def retry_failed(bulk_message):
	"""
	Queue a re-send of every Failed message of this batch.

	Parameters:
		bulk_message (Document, required): Bulk WhatsApp Message.

	Returns:
		None
	"""
	failed_messages = frappe.get_all(
		"WhatsApp Message",
		filters={"bulk_message_reference": bulk_message.name, "status": "Failed"},
		pluck="name",
	)
	for message_name in failed_messages:
		frappe.enqueue_doc(
			bulk_message.doctype, bulk_message.name, "resend_single_message", "long", 4000, message_name=message_name
		)

	frappe.msgprint(_("{0} message(s) requeued for sending").format(len(failed_messages)))


def resend_single_message(message_name):
	"""
	Background job: send a Failed WhatsApp Message again.

	The first send only happens in before_insert, so an existing message is
	sent again directly. Its old message_id is cleared because template
	sends skip messages that already have one.

	Parameters:
		message_name (str, required): WhatsApp Message name.

	Returns:
		None
	"""
	message = frappe.get_doc("WhatsApp Message", message_name)
	message.message_id = None
	message.status = "Queued"
	message.db_update()

	try:
		message.send_outgoing()
		message.status = "Success"
	except Exception:
		message.status = "Failed"
		frappe.log_error(title=f"WhatsApp bulk retry failed: {message.name}")

	message.db_update()


def get_progress(bulk_message):
	"""
	How many messages of the batch were sent, failed or are still queued.

	Parameters:
		bulk_message (Document, required): Bulk WhatsApp Message.

	Returns:
		dict: {"total", "sent", "failed", "queued", "percent"}
	"""
	total = bulk_message.recipient_count
	sent = count_messages(bulk_message.name, ["in", SENT_STATUSES])
	failed = count_messages(bulk_message.name, "Failed")
	queued = count_messages(bulk_message.name, "Queued")

	return {
		"total": total,
		"sent": sent,
		"failed": failed,
		"queued": queued,
		"percent": (sent / total * 100) if total else 0,
	}


def count_messages(bulk_message_name, status):
	"""
	Count the batch's WhatsApp Messages with a status.

	Parameters:
		bulk_message_name (str, required): Bulk WhatsApp Message name.
		status (str | list, required): Status, or a filter like ["in", [...]].

	Returns:
		int: Count.
	"""
	return frappe.db.count("WhatsApp Message", {"bulk_message_reference": bulk_message_name, "status": status})


def get_bulk_progress(bulk_message_name):
	"""
	Progress of a Bulk WhatsApp Message the user can read.

	Parameters:
		bulk_message_name (str, required): Bulk WhatsApp Message name.

	Returns:
		dict: Progress counts.
	"""
	bulk_message = frappe.get_doc("Bulk WhatsApp Message", bulk_message_name)
	bulk_message.check_permission("read")
	return bulk_message.get_progress()


def retry_bulk_failed(bulk_message_name):
	"""
	Re-send the Failed messages of a Bulk WhatsApp Message the user can edit.

	Parameters:
		bulk_message_name (str, required): Bulk WhatsApp Message name.

	Returns:
		None
	"""
	bulk_message = frappe.get_doc("Bulk WhatsApp Message", bulk_message_name)
	bulk_message.check_permission("write")
	bulk_message.retry_failed()
