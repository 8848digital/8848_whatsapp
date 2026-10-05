# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Endpoints behind the Bulk WhatsApp Message and WhatsApp Recipient List forms."""

import frappe

from frappe_whatsapp.frappe_whatsapp.doctype.bulk_whatsapp_message.bulk_progress import get_bulk_progress, retry_bulk_failed
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_recipient_list.recipient_import import import_into_list


@frappe.whitelist()
def get_progress(name: str):
	"""
	Sending progress of a Bulk WhatsApp Message, for its progress bar.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.bulk_messaging.get_progress`
	**HTTP Method:** GET, POST
	**Parameters:**
		- name (str, required): Bulk WhatsApp Message name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": {"total": 100, "sent": 90, "failed": 4, "queued": 6, "percent": 90.0}, "errors": null}
```
	"""
	return get_bulk_progress(name)


@frappe.whitelist(methods=["POST"])
def retry_failed(name: str):
	"""
	Queue a re-send of every Failed message of a Bulk WhatsApp Message.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.bulk_messaging.retry_failed`
	**HTTP Method:** POST
	**Parameters:**
		- name (str, required): Bulk WhatsApp Message name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": true, "errors": null}
```
	"""
	retry_bulk_failed(name)
	return True


@frappe.whitelist(methods=["POST"])
def import_recipients(
	list_name: str,
	doctype: str,
	mobile_field: str,
	name_field: str | None = None,
	filters: str | dict | None = None,
	limit: int | None = None,
	data_fields: str | list | None = None,
):
	"""
	Fill a WhatsApp Recipient List from the records of another DocType,
	keeping chosen fields per recipient as template variables.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.bulk_messaging.import_recipients`
	**HTTP Method:** POST
	**Parameters:**
		- list_name (str, required): WhatsApp Recipient List name
		- doctype (str, required): DocType to read, e.g. "Customer"
		- mobile_field (str, required): Field with the mobile number
		- name_field (str, optional): Field with the recipient's name
		- filters (dict | JSON str, optional): Record filters
		- limit (int, optional): Maximum records to import
		- data_fields (list | JSON str, optional): Fields kept as template variables
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": 25, "errors": null}
```
	"""
	return import_into_list(list_name, doctype, mobile_field, name_field, filters, limit, data_fields)
