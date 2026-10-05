# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Endpoints for WhatsApp Account set-up."""

import frappe

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_account.account_utils import subscribe_account


@frappe.whitelist(methods=["POST"])
def subscribe_app(account: str):
	"""
	Subscribe the Meta app to a WhatsApp Account's webhooks so incoming
	messages start arriving. Run once after registering the phone number.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.account.subscribe_app`
	**HTTP Method:** POST
	**Parameters:**
		- account (str, required): WhatsApp Account name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": {"success": true}, "errors": null}
```
	"""
	return subscribe_account(account)
