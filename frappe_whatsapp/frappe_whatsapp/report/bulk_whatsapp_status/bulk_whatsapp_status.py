# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, Shridhar Patil and contributors
# For license information, please see license.txt

import frappe

# Report column -> WhatsApp Message status it counts.
STATUS_COUNTS = {
	"delivered_count": "delivered",
	"read_count": "read",
	"sent_count": "sent",
	"failed_count": "failed",
}


def execute(filters=None):
	"""
	Bulk WhatsApp Status: each submitted bulk message with its delivery counts.

	Parameters:
		filters (dict, optional): from_date, to_date, status, from_number.

	Returns:
		tuple: (columns, data)
	"""
	return get_columns(), get_data(filters or {})


def get_columns():
	"""
	Report columns.

	Returns:
		list: Column definitions.
	"""
	return [
		{"fieldname": "name", "label": "ID", "fieldtype": "Link", "options": "Bulk WhatsApp Message", "width": 120},
		{"fieldname": "title", "label": "Title", "fieldtype": "Data", "width": 180},
		{"fieldname": "creation", "label": "Created On", "fieldtype": "Datetime", "width": 150},
		{"fieldname": "recipient_count", "label": "Total Recipients", "fieldtype": "Int", "width": 120},
		{"fieldname": "sent_count", "label": "Messages Sent", "fieldtype": "Int", "width": 120},
		{"fieldname": "delivered_count", "label": "Delivered", "fieldtype": "Int", "width": 100},
		{"fieldname": "read_count", "label": "Read", "fieldtype": "Int", "width": 100},
		{"fieldname": "failed_count", "label": "Failed", "fieldtype": "Int", "width": 100},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 120},
	]


def get_data(filters):
	"""
	Submitted bulk messages, newest first, with message counts per delivery status.

	Parameters:
		filters (dict, required): Report filters.

	Returns:
		list: Rows.
	"""
	query_filters = {"docstatus": 1}
	if filters.get("from_date") and filters.get("to_date"):
		query_filters["creation"] = ["between", [filters["from_date"], filters["to_date"]]]
	if filters.get("status"):
		query_filters["status"] = filters["status"]
	if filters.get("from_number"):
		query_filters["from_number"] = filters["from_number"]

	rows = frappe.get_all(
		"Bulk WhatsApp Message",
		filters=query_filters,
		fields=["name", "title", "creation", "recipient_count", "sent_count", "status"],
		order_by="creation desc",
	)

	for row in rows:
		row.update(get_status_counts(row.name))

	return rows


def get_status_counts(bulk_message_name):
	"""
	How many of a bulk message's WhatsApp Messages are in each delivery status.

	Parameters:
		bulk_message_name (str, required): Bulk WhatsApp Message name.

	Returns:
		dict: {"delivered_count": int, "read_count": int, "sent_count": int, "failed_count": int}
	"""
	counts = {}
	for column, status in STATUS_COUNTS.items():
		counts[column] = frappe.db.count(
			"WhatsApp Message", {"bulk_message_reference": bulk_message_name, "status": status}
		)

	return counts
