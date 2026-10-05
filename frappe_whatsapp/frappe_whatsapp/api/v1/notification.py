# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Endpoints for WhatsApp Notifications."""

import frappe

from frappe_whatsapp.frappe_whatsapp.tasks import send_date_based_notifications


@frappe.whitelist(methods=["POST"])
def call_trigger_notifications():
	"""
	Send today's "Days Before" / "Days After" notifications now instead of
	waiting for the daily scheduler (the "Get Alerts for Today" button).

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.notification.call_trigger_notifications`
	**HTTP Method:** POST
	**Parameters:** None
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": null, "errors": null}
```
	"""
	try:
		send_date_based_notifications()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in call_trigger_notifications")
		raise
