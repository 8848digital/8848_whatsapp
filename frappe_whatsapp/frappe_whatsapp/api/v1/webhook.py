# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Webhook endpoint registered in Meta's App Dashboard."""

import frappe

from frappe_whatsapp.utils.webhook import handle_event, verify_subscription


@frappe.whitelist(allow_guest=True)
def webhook():
	"""
	Receive Meta's webhook: the subscription check (GET) and every event (POST).
	POST events are incoming messages, delivery statuses and template status
	changes; they are logged and saved as WhatsApp Messages or status updates.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.webhook.webhook`
	(the old `/api/method/frappe_whatsapp.utils.webhook.webhook` URL still works,
	see override_whitelisted_methods in hooks.py)
	**HTTP Method:** GET, POST
	**Parameters:**
		- hub.mode (str, required for GET): "subscribe"
		- hub.verify_token (str, required for GET): Must match a WhatsApp Account's Webhook Verify Token
		- hub.challenge (str, required for GET): Echoed back to Meta
		- entry (list, required for POST): Meta's event payload
	**Response:**
	GET returns the hub.challenge value as plain text. POST returns:
```json
		{}
```
	"""
	if frappe.request.method == "GET":
		return verify_subscription(frappe.form_dict)

	handle_event(frappe.local.form_dict)
