# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Default-account handling and webhook subscription for WhatsApp Account."""

import frappe
from frappe import _
from frappe.integrations.utils import make_post_request

from frappe_whatsapp.utils.meta_api import get_auth_headers, get_graph_url, get_meta_error

DEFAULT_FIELDS = ("is_default_incoming", "is_default_outgoing")


def keep_single_default(account):
	"""
	When this account is a default, un-tick the same default on every other account.

	Parameters:
		account (Document, required): The WhatsApp Account just saved.

	Returns:
		None
	"""
	for field in DEFAULT_FIELDS:
		if account.get(field):
			clear_default_on_other_accounts(account.name, field)


def clear_default_on_other_accounts(account_name, field):
	"""
	Un-tick a default checkbox on every account except this one.

	Uses db.set_value, not save: saving the other account would run its
	on_update, which can clear the default on this account again.

	Parameters:
		account_name (str, required): The account that keeps the default.
		field (str, required): "is_default_incoming" or "is_default_outgoing".

	Returns:
		None
	"""
	other_accounts = frappe.get_all("WhatsApp Account", filters={field: 1, "name": ("!=", account_name)}, pluck="name")
	for other_account_name in other_accounts:
		frappe.db.set_value("WhatsApp Account", other_account_name, field, 0)


def subscribe_app_to_webhooks(account):
	"""
	Subscribe the Meta app to this business account's webhooks.

	Needed once after the phone number is registered, otherwise incoming
	messages never reach the webhook. Calls POST /{business_id}/subscribed_apps.

	Parameters:
		account (Document, required): WhatsApp Account with url, version, business_id and token.

	Returns:
		dict: Meta's response, e.g. {"success": true}.
	"""
	for field in ("url", "version", "business_id"):
		if not account.get(field):
			frappe.throw(
				_("{0} is required to subscribe the app").format(frappe.bold(account.meta.get_label(field)))
			)

	if not account.get_password("token"):
		frappe.throw(_("Access token is required to subscribe the app"))

	try:
		response = make_post_request(
			get_graph_url(account, f"{account.business_id}/subscribed_apps"),
			headers=get_auth_headers(account),
		)
	except Exception as e:
		error = get_meta_error()
		error_message = error.get("message") or error.get("Error") or str(e)
		frappe.throw(_("Failed to subscribe app to webhooks: {0}").format(error_message))

	if not response.get("success"):
		frappe.throw(_("Subscription was not successful: {0}").format(frappe.as_json(response)))

	frappe.logger().info(f"WhatsApp app subscribed to webhooks for business_id={account.business_id}")
	return response


def subscribe_account(account_name):
	"""
	Load a WhatsApp Account the user can read and subscribe it to webhooks.

	Parameters:
		account_name (str, required): WhatsApp Account name.

	Returns:
		dict: Meta's response.
	"""
	account = frappe.get_doc("WhatsApp Account", account_name)
	account.check_permission("read")

	return subscribe_app_to_webhooks(account)
