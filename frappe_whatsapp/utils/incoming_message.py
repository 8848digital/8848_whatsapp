# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Save one incoming webhook message as a WhatsApp Message."""

import json

import frappe
import requests
from frappe import _

from frappe_whatsapp.utils.meta_api import get_graph_url

MEDIA_TYPES = ("image", "audio", "video", "document")


def save_incoming_message(message, account, profile_name):
	"""
	Save a message from Meta's webhook, based on its type.

	Parameters:
		message (dict, required): One entry of value["messages"] from the webhook.
		account (Document, required): WhatsApp Account that received it.
		profile_name (str, optional): Sender's WhatsApp profile name.

	Returns:
		None
	"""
	message_type = message["type"]
	values = get_base_values(message, account, profile_name)

	if message_type == "text":
		values.update(get_reply_values(message))
		values.update(message=message["text"]["body"], content_type=message_type)
		insert_message(values)
	elif message_type == "reaction":
		values.update(
			message=message["reaction"]["emoji"],
			reply_to_message_id=message["reaction"]["message_id"],
			content_type="reaction",
		)
		insert_message(values)
	elif message_type == "interactive":
		save_interactive_message(message, values)
	elif message_type == "order":
		values.update(
			message=_("New Order Received via WhatsApp"),
			content_type="order",
			product_catalog_json=json.dumps(message["order"]),
		)
		insert_message(values)
	elif message_type in MEDIA_TYPES:
		save_media_message(message, values, account)
	elif message_type == "button":
		values.update(get_reply_values(message))
		values.update(message=message["button"]["text"], content_type=message_type)
		insert_message(values)
	else:
		values.update(message=message[message_type].get(message_type), content_type=message_type)
		insert_message(values)


def save_interactive_message(message, values):
	"""
	Save a button reply, list reply or completed Flow (nfm_reply).

	Parameters:
		message (dict, required): Webhook message of type "interactive".
		values (dict, required): Base WhatsApp Message values for this message.

	Returns:
		None
	"""
	interactive = message["interactive"]
	interactive_type = interactive.get("type")
	values.update(get_reply_values(message))

	if interactive_type == "button_reply":
		values.update(message=interactive["button_reply"]["id"], content_type="button")
		insert_message(values)
	elif interactive_type == "list_reply":
		values.update(message=interactive["list_reply"]["id"], content_type="button")
		insert_message(values)
	elif interactive_type == "nfm_reply":
		save_flow_reply(message, interactive["nfm_reply"], values)


def save_flow_reply(message, nfm_reply, values):
	"""
	Save the answers of a completed WhatsApp Flow and tell open chat screens.

	Parameters:
		message (dict, required): Webhook message carrying the flow reply.
		nfm_reply (dict, required): The "nfm_reply" part, with "response_json".
		values (dict, required): Base WhatsApp Message values for this message.

	Returns:
		None
	"""
	try:
		flow_response = json.loads(nfm_reply.get("response_json", "{}"))
	except json.JSONDecodeError:
		flow_response = {}

	summary_parts = []
	for key, value in flow_response.items():
		if value:
			summary_parts.append(f"{key}: {value}")

	values.update(
		message=", ".join(summary_parts) if summary_parts else "Flow completed",
		content_type="flow",
		flow_response=json.dumps(flow_response),
	)
	insert_message(values)

	# nosemgrep: frappe-realtime-pick-room -- intentional site-wide fan-out for chat UIs (whatsapp_chat companion app) listening for inbound flow responses
	frappe.publish_realtime(
		"whatsapp_flow_response",
		{
			"phone": message["from"],
			"message_id": message["id"],
			"flow_response": flow_response,
			"whatsapp_account": values["whatsapp_account"],
		},
	)


def save_media_message(message, values, account):
	"""
	Download an image, audio, video or document from Meta and attach it to a new message.

	Nothing is saved when Meta doesn't return the file.

	Parameters:
		message (dict, required): Webhook message of a media type.
		values (dict, required): Base WhatsApp Message values for this message.
		account (Document, required): WhatsApp Account whose token can read the media.

	Returns:
		None
	"""
	message_type = message["type"]
	headers = {"Authorization": "Bearer " + account.get_password("token")}

	media_info = requests.get(get_graph_url(account, f"{message[message_type]['id']}/"), headers=headers)
	if media_info.status_code != 200:
		return

	media_data = media_info.json()
	file_extension = media_data.get("mime_type").split("/")[1]

	media_file = requests.get(media_data.get("url"), headers=headers)
	if media_file.status_code != 200:
		return

	values.update(get_reply_values(message))
	values.update(message=message[message_type].get("caption", ""), content_type=message_type)
	message_doc = insert_message(values)

	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{frappe.generate_hash(length=10)}.{file_extension}",
			"attached_to_doctype": "WhatsApp Message",
			"attached_to_name": message_doc.name,
			"content": media_file.content,
			"attached_to_field": "attach",
		}
	).save(ignore_permissions=True)

	message_doc.attach = file_doc.file_url
	message_doc.save()


def get_base_values(message, account, profile_name):
	"""
	Fields every incoming WhatsApp Message gets.

	Parameters:
		message (dict, required): Webhook message.
		account (Document, required): WhatsApp Account that received it.
		profile_name (str, optional): Sender's WhatsApp profile name.

	Returns:
		dict: WhatsApp Message values.
	"""
	return {
		"doctype": "WhatsApp Message",
		"type": "Incoming",
		"from": message["from"],
		"message_id": message["id"],
		"profile_name": profile_name,
		"whatsapp_account": account.name,
	}


def get_reply_values(message):
	"""
	Reply details for a message sent as a reply (forwarded messages don't count).

	Parameters:
		message (dict, required): Webhook message.

	Returns:
		dict: {"is_reply": bool, "reply_to_message_id": str | None}
	"""
	context = message.get("context")
	is_reply = bool(context) and "forwarded" not in context

	return {
		"is_reply": is_reply,
		"reply_to_message_id": context["id"] if is_reply else None,
	}


def insert_message(values):
	"""
	Insert a WhatsApp Message as the webhook (a guest request).

	Parameters:
		values (dict, required): WhatsApp Message values including "doctype".

	Returns:
		Document: The new WhatsApp Message.
	"""
	return frappe.get_doc(values).insert(ignore_permissions=True)
