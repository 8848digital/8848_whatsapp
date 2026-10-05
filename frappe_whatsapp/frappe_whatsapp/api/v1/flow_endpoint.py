# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Data-exchange endpoint for WhatsApp Flows that need a server."""

import frappe

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_data_exchange import handle_flow_request as handle


@frappe.whitelist(allow_guest=True)
def handle_flow_request():
	"""
	Answer WhatsApp when a Flow opens, moves between screens or pings the endpoint.
	Flows built in this app are client-only, so this mostly acknowledges
	requests; form data received here is stored for later processing.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow_endpoint.handle_flow_request`
	(the old `/api/method/frappe_whatsapp.frappe_whatsapp.api.flow_endpoint.handle_flow_request`
	URL still works, see override_whitelisted_methods in hooks.py)
	**HTTP Method:** GET (health check), POST (flow request)
	**Parameters:**
		- action (str, required for POST): "ping", "INIT", "data_exchange" or "BACK"
		- flow_token (str, optional): Token sent with the flow message
		- screen (str, optional): Current screen id
		- data (dict, optional): Form values from the screen
	**Response:**
```json
		{"screen": "INIT", "data": {}}
```
	"""
	return handle(frappe.request.method, frappe.request.get_json(silent=True))
