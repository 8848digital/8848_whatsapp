# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Endpoints for WhatsApp Templates."""

import frappe

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_fetch import fetch_templates_from_meta


@frappe.whitelist()
def fetch():
	"""
	Pull every template of every active WhatsApp Account from Meta into
	WhatsApp Templates, creating new ones and updating existing ones.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.template.fetch`
	**HTTP Method:** POST
	**Parameters:** None
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": "Successfully fetched templates from meta", "errors": null}
```
	"""
	return fetch_templates_from_meta()
