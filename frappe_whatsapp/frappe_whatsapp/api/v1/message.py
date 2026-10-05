# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Endpoints for sending WhatsApp Messages from the desk."""

import frappe

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message.message_utils import (
	create_template_message,
	mark_message_as_read,
)


@frappe.whitelist()
def send_template(to: str, reference_doctype: str, reference_name: str, template: str):
	"""
	Send a WhatsApp Template about a document, e.g. from the "Send To Whatsapp" dialog.
	The template's placeholders are filled from the reference document.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.message.send_template`
	**HTTP Method:** POST
	**Parameters:**
		- to (str, required): Recipient's number with country code
		- reference_doctype (str, required): DocType the message is about
		- reference_name (str, required): Document the message is about
		- template (str, required): WhatsApp Template name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": null, "errors": null}
```
	"""
	create_template_message(to, reference_doctype, reference_name, template)


@frappe.whitelist()
def send_read_receipt(message: str):
	"""
	Mark an incoming WhatsApp Message as read on the customer's phone.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.message.send_read_receipt`
	**HTTP Method:** POST
	**Parameters:**
		- message (str, required): WhatsApp Message name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": true, "errors": null}
```
	"""
	return mark_message_as_read(message)
