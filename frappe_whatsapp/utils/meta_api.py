# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Small helpers for talking to Meta's WhatsApp Cloud (Graph) API."""

import json

import frappe
from frappe.integrations.utils import make_post_request


def get_whatsapp_account(phone_id=None, account_type="incoming"):
	"""
	Find the WhatsApp Account for a phone number id, or the default one.

	Parameters:
		phone_id (str, optional): Meta phone number id from a webhook or message.
		account_type (str, optional): "incoming" or "outgoing"; picks which default to use.

	Returns:
		Document | None: The WhatsApp Account, or None when nothing matches.
	"""
	if phone_id:
		account_name = frappe.db.get_value("WhatsApp Account", {"phone_id": phone_id}, "name")
		if account_name:
			return frappe.get_doc("WhatsApp Account", account_name)

	if account_type == "incoming":
		default_field = "is_default_incoming"
	else:
		default_field = "is_default_outgoing"

	default_account_name = frappe.db.get_value("WhatsApp Account", {default_field: 1}, "name")
	if default_account_name:
		return frappe.get_doc("WhatsApp Account", default_account_name)

	return None


def get_auth_headers(account, json_body=True):
	"""
	Build the authorization headers for a Graph API call.

	Parameters:
		account (Document, required): WhatsApp Account holding the access token.
		json_body (bool, optional): Also send a JSON content-type header.

	Returns:
		dict: Request headers.
	"""
	headers = {"authorization": f"Bearer {account.get_password('token')}"}
	if json_body:
		headers["content-type"] = "application/json"

	return headers


def get_graph_url(account, path):
	"""
	Build a Graph API URL for an account, e.g. ".../v19.0/<phone_id>/messages".

	Parameters:
		account (Document, required): WhatsApp Account with url and version.
		path (str, required): Path after the version, without a leading slash.

	Returns:
		str: Full URL.
	"""
	return f"{account.url}/{account.version}/{path}"


def post_message(account, data):
	"""
	Send a message payload through an account's phone number.

	Parameters:
		account (Document, required): WhatsApp Account to send from.
		data (dict, required): Message payload in Meta's format.

	Returns:
		dict: Meta's response, e.g. {"messages": [{"id": "wamid..."}]}.
	"""
	return make_post_request(
		get_graph_url(account, f"{account.phone_id}/messages"),
		headers=get_auth_headers(account),
		data=json.dumps(data),
	)


def get_meta_response():
	"""
	Read the JSON body of the last request Frappe made to Meta.

	Frappe keeps the last integration response on frappe.flags, which is
	where Meta's error details live after make_post_request raises.

	Returns:
		dict: The response body, or {} when there is none.
	"""
	response = frappe.flags.integration_request
	# A requests Response is falsy for 4xx/5xx, so check for None, not truthiness.
	if response is None or not hasattr(response, "json"):
		return {}

	try:
		return response.json() or {}
	except ValueError:
		return {}


def get_meta_error():
	"""
	The "error" part of Meta's last response.

	Returns:
		dict: Meta's error details, e.g. {"message": ..., "error_user_title": ...}, or {}.
	"""
	return get_meta_response().get("error") or {}
