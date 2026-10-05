# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""
Handle Meta's webhook: subscription check, incoming messages and status updates.

The whitelisted endpoint Meta calls lives in
frappe_whatsapp.frappe_whatsapp.api.v1.webhook; this file holds the logic.
"""

import json

import frappe
from werkzeug.wrappers import Response

from frappe_whatsapp.utils.incoming_message import save_incoming_message
from frappe_whatsapp.utils.meta_api import get_whatsapp_account


def verify_subscription(form_dict):
	"""
	Answer Meta's GET check when the webhook URL is registered.

	Parameters:
		form_dict (dict, required): Query params with "hub.challenge" and "hub.verify_token".

	Returns:
		Response: The challenge echoed back as plain text.
	"""
	verify_token = form_dict.get("hub.verify_token")
	webhook_verify_token = frappe.db.get_value(
		"WhatsApp Account", {"webhook_verify_token": verify_token}, "webhook_verify_token"
	)
	if not webhook_verify_token:
		frappe.throw("No matching WhatsApp account")

	if verify_token != webhook_verify_token:
		frappe.throw("Verify token does not match")

	return Response(form_dict.get("hub.challenge"), status=200)


def handle_event(data):
	"""
	Process a webhook POST: save incoming messages, or apply status updates.

	Every event is logged first, so nothing Meta sends is lost even if
	processing fails.

	Parameters:
		data (dict, required): The webhook body.

	Returns:
		None
	"""
	frappe.get_doc(
		{"doctype": "WhatsApp Notification Log", "template": "Webhook", "meta_data": json.dumps(data)}
	).insert(ignore_permissions=True)

	messages, phone_id = get_messages_and_phone_id(data)

	if not messages:
		update_status(get_first_change(data))
		return

	# Only message events carry metadata.phone_number_id. Status events
	# (template status, delivery receipts) have none, which is why the account
	# check guards just this branch and not the status updates above.
	account = get_whatsapp_account(phone_id) if phone_id else None
	if not account:
		return

	profile_name = get_sender_profile_name(data)
	for message in messages:
		save_incoming_message(message, account, profile_name)


def get_messages_and_phone_id(data):
	"""
	Pull the messages and receiving phone number id out of the webhook body.

	Meta normally sends "entry" as a list; some test payloads send it as a
	single object, which the KeyError fallback handles.

	Parameters:
		data (dict, required): The webhook body.

	Returns:
		tuple: (messages list, phone_number_id or None)
	"""
	try:
		value = data["entry"][0]["changes"][0]["value"]
		return value.get("messages", []), value.get("metadata", {}).get("phone_number_id")
	except KeyError:
		return data["entry"]["changes"][0]["value"].get("messages", []), None


def get_first_change(data):
	"""
	The first change object of the webhook body (status updates come one at a time).

	Parameters:
		data (dict, required): The webhook body.

	Returns:
		dict: e.g. {"field": "messages", "value": {...}}
	"""
	try:
		return data["entry"][0]["changes"][0]
	except KeyError:
		return data["entry"]["changes"][0]


def get_sender_profile_name(data):
	"""
	The sender's WhatsApp profile name, from the first contact that has one.

	Parameters:
		data (dict, required): The webhook body.

	Returns:
		str | None: Profile name.
	"""
	changes = []
	for entry in data.get("entry", []):
		changes.extend(entry.get("changes", []))

	for change in changes:
		contacts = change.get("value", {}).get("contacts", [])
		if contacts:
			return contacts[0].get("profile", {}).get("name")

	return None


def update_status(change):
	"""
	Apply a template-status or message-status update from Meta.

	Parameters:
		change (dict, required): A change with "field" and "value".

	Returns:
		None
	"""
	if change.get("field") == "message_template_status_update":
		update_template_status(change["value"])
	elif change.get("field") == "messages":
		update_message_status(change["value"])


def update_template_status(data):
	"""
	Copy Meta's approval status onto the matching WhatsApp Template.

	Parameters:
		data (dict, required): Has "event" (new status) and "message_template_id".

	Returns:
		None
	"""
	frappe.db.sql(
		"""UPDATE `tabWhatsApp Templates`
		SET status = %(event)s
		WHERE id = %(message_template_id)s""",
		data,
	)


def update_message_status(data):
	"""
	Copy a delivery status (sent, delivered, read...) onto the WhatsApp Message.

	Parameters:
		data (dict, required): Has "statuses": [{"id", "status", "conversation"}].

	Returns:
		None
	"""
	status_update = data["statuses"][0]
	message_name = frappe.db.get_value("WhatsApp Message", filters={"message_id": status_update["id"]})

	message_doc = frappe.get_doc("WhatsApp Message", message_name)
	message_doc.status = status_update["status"]
	conversation_id = status_update.get("conversation", {}).get("id")
	if conversation_id:
		message_doc.conversation_id = conversation_id
	message_doc.save(ignore_permissions=True)
