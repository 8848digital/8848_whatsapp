# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""
Turn a WhatsApp Flow's screens and fields into WhatsApp's Flow JSON.

The flows are client-only: no routing_model or data_api_version is set, so
no endpoint is needed and the answers come back through the webhook
(nfm_reply) when the user finishes.
"""

import frappe
from frappe import _

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_components import build_input_component
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_screens import (
	get_field_references,
	get_next_screen,
	get_screen_fields,
)

TEXT_TYPES = ("TextHeading", "TextSubheading", "TextBody", "TextCaption")


def validate_screens(flow):
	"""
	A flow needs at least one screen, unique screen ids and at least one terminal screen.

	Parameters:
		flow (Document, required): WhatsApp Flow.

	Returns:
		None
	"""
	if not flow.screens:
		frappe.throw(_("At least one screen is required"))

	screen_ids = []
	for screen in flow.screens:
		if screen.screen_id in screen_ids:
			frappe.throw(_("Duplicate screen ID: {0}").format(screen.screen_id))
		screen_ids.append(screen.screen_id)

	if not any(screen.terminal for screen in flow.screens):
		frappe.throw(_("At least one screen must be marked as terminal"))


def generate_flow_json(flow):
	"""
	Build the Flow JSON for WhatsApp.

	Parameters:
		flow (Document, required): WhatsApp Flow.

	Returns:
		dict: {"version": "6.0", "screens": [...]}
	"""
	incoming_data = get_incoming_data(flow)

	screens = []
	for screen in flow.screens:
		screens.append(build_screen(flow, screen, incoming_data.get(screen.screen_id, {})))

	return {"version": flow.data_api_version or "6.0", "screens": screens}


def get_incoming_data(flow):
	"""
	Fields each screen receives from the screens before it.

	Parameters:
		flow (Document, required): WhatsApp Flow.

	Returns:
		dict: {screen_id: {field_name: {"type": "string", "__example__": ""}}}
	"""
	incoming_data = {}
	collected_fields = {}

	for screen in flow.screens:
		if collected_fields:
			incoming_data[screen.screen_id] = collected_fields.copy()

		collected_fields.update(get_field_references(flow, screen.screen_id, None))

	return incoming_data


def build_screen(flow, screen, incoming_data=None):
	"""
	One screen definition with its layout.

	Parameters:
		flow (Document, required): WhatsApp Flow.
		screen (Document, required): WhatsApp Flow Screen row.
		incoming_data (dict, optional): Data the screen receives.

	Returns:
		dict: Screen definition.
	"""
	screen_json = {
		"id": screen.screen_id,
		"title": screen.screen_title,
		"data": incoming_data or {},
		"layout": {"type": "SingleColumnLayout", "children": build_screen_children(flow, screen)},
	}

	if screen.terminal:
		screen_json["terminal"] = True
		screen_json["success"] = True

	if screen.refresh_on_back:
		screen_json["refresh_on_back"] = True

	return screen_json


def build_screen_children(flow, screen):
	"""
	Components of a screen, plus a Footer button when none was added (WhatsApp requires one).

	Parameters:
		flow (Document, required): WhatsApp Flow.
		screen (Document, required): WhatsApp Flow Screen row.

	Returns:
		list: Components.
	"""
	children = []
	has_footer = False

	for field in get_screen_fields(flow, screen.screen_id):
		children.append(build_component(flow, field, screen))
		if field.field_type == "Footer":
			has_footer = True

	if not has_footer:
		children.append(
			{
				"type": "Footer",
				"label": "Complete" if screen.terminal else "Continue",
				"on-click-action": build_footer_action(flow, screen),
			}
		)

	return children


def build_component(flow, field, screen):
	"""
	One component in WhatsApp's format.

	Parameters:
		flow (Document, required): WhatsApp Flow.
		field (Document, required): WhatsApp Flow Field row.
		screen (Document, required): The field's screen.

	Returns:
		dict: Component.
	"""
	field_type = field.field_type

	if field_type in TEXT_TYPES:
		return {"type": field_type, "text": field.label or ""}

	if field_type == "Image":
		component = {"type": "Image", "src": field.init_value or ""}
		if field.label:
			component["alt-text"] = field.label
		return component

	if field_type == "EmbeddedLink":
		return {
			"type": "EmbeddedLink",
			"text": field.label or "Link",
			"on-click-action": {"name": "navigate", "next": {"type": "screen", "name": field.init_value or ""}},
		}

	if field_type == "Footer":
		return {"type": "Footer", "label": field.label or "Submit", "on-click-action": build_footer_action(flow, screen)}

	return build_input_component(field)


def build_footer_action(flow, screen):
	"""
	Footer action: go to the next screen, or complete the flow on the last/terminal one.

	Parameters:
		flow (Document, required): WhatsApp Flow.
		screen (Document, required): Current screen.

	Returns:
		dict: on-click-action.
	"""
	next_screen = None if screen.terminal else get_next_screen(flow, screen)
	if not next_screen:
		return {"name": "complete", "payload": build_payload(flow, screen)}

	return {
		"name": "navigate",
		"next": {"type": "screen", "name": next_screen.screen_id},
		"payload": build_payload(flow, screen),
	}


def build_payload(flow, screen):
	"""
	Values passed on from this screen: earlier screens' fields as ${data.x}, this screen's as ${form.x}.

	Parameters:
		flow (Document, required): WhatsApp Flow.
		screen (Document, required): Current screen.

	Returns:
		dict: e.g. {"name": "${data.name}", "date": "${form.date}"}
	"""
	payload = {}
	for each_screen in flow.screens:
		is_current = each_screen.screen_id == screen.screen_id
		payload.update(get_field_references(flow, each_screen.screen_id, "form" if is_current else "data"))
		if is_current:
			break

	return payload
