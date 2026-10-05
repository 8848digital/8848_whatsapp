# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Replies to WhatsApp Flow data-exchange requests (see api/v1/flow_endpoint.py)."""

import json

import frappe
from frappe import _


def handle_flow_request(method, data):
	"""
	Work out the reply for one Flow endpoint request.

	Errors are returned inside the reply instead of raised, because WhatsApp
	only reads the JSON body.

	Parameters:
		method (str, required): HTTP method of the request.
		data (dict, optional): Parsed JSON body of a POST.

	Returns:
		dict: Reply for WhatsApp, e.g. {"screen": "INIT", "data": {}}.
	"""
	try:
		if method == "GET":
			# WhatsApp pings the endpoint with a GET to check it is up.
			return {"status": "ok"}

		if not data:
			frappe.throw(_("No data received"))

		frappe.log_error(f"WhatsApp Flow Request:\n{json.dumps(data, indent=2)}", "WhatsApp Flow Endpoint")

		action = data.get("action")
		if action == "ping":
			return {"data": {"status": "active"}}
		if action == "INIT":
			return {"screen": data.get("screen") or "INIT", "data": {}}
		if action == "data_exchange":
			if data.get("flow_token"):
				save_flow_data(data.get("flow_token"), data.get("screen"), data.get("data", {}))
			return {"data": {}}

		# "BACK" and anything unknown need no data.
		return {"data": {}}

	except Exception as e:
		frappe.log_error(f"Flow endpoint error: {str(e)}", "WhatsApp Flow Error")
		return {"data": {"error": str(e)}}


def save_flow_data(flow_token, screen, form_data):
	"""
	Merge form values into the "WhatsApp Flow Data" record for this flow token.

	That DocType isn't part of this app; a site can add it to keep partial
	answers. Without it the values are written to the Error Log instead.

	Parameters:
		flow_token (str, required): Token identifying one flow session.
		screen (str, optional): Screen the values came from.
		form_data (dict, required): Field values from the screen.

	Returns:
		None
	"""
	try:
		existing = frappe.db.exists("WhatsApp Flow Data", {"flow_token": flow_token})
		if not existing:
			frappe.log_error(
				f"Flow Token: {flow_token}\nScreen: {screen}\nData: {json.dumps(form_data)}",
				"WhatsApp Flow Data",
			)
			return

		flow_data = frappe.get_doc("WhatsApp Flow Data", existing)
		saved_values = json.loads(flow_data.data or "{}")
		saved_values.update(form_data)
		flow_data.data = json.dumps(saved_values)
		flow_data.last_screen = screen
		flow_data.save(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(f"save_flow_data error: {str(e)}")
