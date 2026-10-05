# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Build the Meta payload for a non-template outgoing WhatsApp Message."""

import json
from urllib.parse import quote

import frappe
from frappe import _

from frappe_whatsapp.utils.phone import format_number

# Meta allows 3 reply buttons; more options are sent as a list of up to 10 rows.
MAX_REPLY_BUTTONS = 3
MAX_LIST_ROWS = 10


def build_outgoing_payload(doc):
	"""
	Build the request body for a text, media, reaction, interactive or flow message.

	Parameters:
		doc (Document, required): Outgoing WhatsApp Message.

	Returns:
		dict: Payload for Meta's /messages endpoint.
	"""
	data = {
		"messaging_product": "whatsapp",
		"to": format_number(doc.to),
		"type": doc.content_type,
	}
	if doc.is_reply and doc.reply_to_message_id:
		data["context"] = {"message_id": doc.reply_to_message_id}

	content_type = doc.content_type
	if content_type in ("document", "image", "video"):
		data[content_type.lower()] = {"link": get_attachment_link(doc), "caption": doc.message}
	elif content_type == "reaction":
		data["reaction"] = {"message_id": doc.reply_to_message_id, "emoji": doc.message}
	elif content_type == "text":
		data["text"] = {"preview_url": True, "body": doc.message}
	elif content_type == "audio":
		data["audio"] = {"link": get_attachment_link(doc)}
	elif content_type == "interactive":
		data["type"] = "interactive"
		data["interactive"] = build_interactive(doc)
	elif content_type == "flow":
		data["type"] = "interactive"
		data["interactive"] = build_flow_interactive(doc)

	return data


def get_attachment_link(doc):
	"""
	Public link to the message's attachment; site files are URL-quoted so names with spaces work.

	Parameters:
		doc (Document, required): WhatsApp Message with an "attach" value.

	Returns:
		str | None: Full URL of the file.
	"""
	if doc.attach and not doc.attach.startswith("http"):
		return frappe.utils.get_url() + "/" + quote(doc.attach)

	return doc.attach


def build_interactive(doc):
	"""
	Reply buttons for up to 3 options, otherwise a list of up to 10 rows.

	Parameters:
		doc (Document, required): WhatsApp Message whose "buttons" holds [{"id", "title", "description"}].

	Returns:
		dict: The "interactive" part of the payload.
	"""
	buttons = json.loads(doc.buttons) if isinstance(doc.buttons, str) else doc.buttons

	if isinstance(buttons, list) and len(buttons) > MAX_REPLY_BUTTONS:
		rows = []
		for button in buttons[:MAX_LIST_ROWS]:
			rows.append(
				{"id": button["id"], "title": button["title"], "description": button.get("description", "")}
			)
		return {
			"type": "list",
			"body": {"text": doc.message},
			"action": {"button": "Select Option", "sections": [{"title": "Options", "rows": rows}]},
		}

	reply_buttons = []
	for button in buttons[:MAX_REPLY_BUTTONS]:
		reply_buttons.append({"type": "reply", "reply": {"id": button["id"], "title": button["title"]}})

	return {"type": "button", "body": {"text": doc.message}, "action": {"buttons": reply_buttons}}


def build_flow_interactive(doc):
	"""
	Interactive part for sending a WhatsApp Flow. Unpublished flows go out in draft mode for testing.

	Parameters:
		doc (Document, required): WhatsApp Message with "flow" set.

	Returns:
		dict: The "interactive" part of the payload.
	"""
	if not doc.flow:
		frappe.throw(_("WhatsApp Flow is required for flow content type"))

	flow = frappe.get_doc("WhatsApp Flow", doc.flow)
	if not flow.flow_id:
		frappe.throw(_("Flow must be created on WhatsApp before sending"))

	flow_screen = doc.flow_screen
	if not flow_screen and flow.screens:
		flow_screen = flow.screens[0].screen_id

	parameters = {
		"flow_message_version": "3",
		"flow_id": flow.flow_id,
		"flow_cta": doc.flow_cta or flow.flow_cta or "Open",
		"flow_action": "navigate",
		"flow_action_payload": {"screen": flow_screen},
	}

	if flow.status != "Published":
		parameters["mode"] = "draft"
		frappe.msgprint(_("Sending flow in draft mode (for testing only)"), indicator="orange")

	# WhatsApp requires a flow token; make one up when none is given.
	parameters["flow_token"] = doc.flow_token or frappe.generate_hash(length=16)

	return {
		"type": "flow",
		"body": {"text": doc.message or "Please fill out the form"},
		"action": {"name": "flow", "parameters": parameters},
	}
