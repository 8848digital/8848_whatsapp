# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Close off Bulk WhatsApp Messages once every message has been attempted."""

import frappe
from frappe.utils import cint


def update_queued_bulk_statuses():
	"""
	Mark queued bulk messages whose messages were all attempted.

	sent_count counts attempts, so a batch is finished when it reaches
	recipient_count; it is Partially Failed when any of its messages failed.

	Returns:
		None
	"""
	queued_bulk_messages = frappe.get_all(
		"Bulk WhatsApp Message",
		filters={"status": "Queued", "docstatus": 1},
		fields=["name", "recipient_count", "sent_count"],
	)

	for bulk_message in queued_bulk_messages:
		if cint(bulk_message.sent_count) < cint(bulk_message.recipient_count):
			continue

		failed_count = frappe.db.count(
			"WhatsApp Message", {"bulk_message_reference": bulk_message.name, "status": "Failed"}
		)
		status = "Partially Failed" if failed_count else "Completed"
		frappe.db.set_value("Bulk WhatsApp Message", bulk_message.name, "status", status)
