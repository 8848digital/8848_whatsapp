# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Turn WhatsApp's Flow JSON back into WhatsApp Flow screen and field rows."""

import json

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_components import OPTION_TYPES


def add_screens_from_json(flow, flow_json):
	"""
	Add screen and field rows to a WhatsApp Flow from WhatsApp's Flow JSON.

	Parameters:
		flow (Document, required): WhatsApp Flow to fill.
		flow_json (dict, required): Parsed Flow JSON.

	Returns:
		None
	"""
	for screen in flow_json.get("screens", []):
		flow.append(
			"screens",
			{
				"screen_id": screen.get("id"),
				"screen_title": screen.get("title", ""),
				"terminal": 1 if screen.get("terminal") else 0,
				"refresh_on_back": 1 if screen.get("refresh_on_back") else 0,
			},
		)

		add_fields_from_screen(flow, screen)


def add_fields_from_screen(flow, screen):
	"""
	Add a field row for every component in one Flow JSON screen.

	Parameters:
		flow (Document, required): WhatsApp Flow to fill.
		screen (dict, required): Screen from the Flow JSON.

	Returns:
		None
	"""
	for component in screen.get("layout", {}).get("children", []):
		if component.get("type"):
			flow.append("fields", get_field_row(screen.get("id"), component))


def get_field_row(screen_id, component):
	"""
	WhatsApp Flow Field values for one Flow JSON component.

	Parameters:
		screen_id (str, required): Screen the component is on.
		component (dict, required): Component from the Flow JSON.

	Returns:
		dict: Field row values.
	"""
	field_type = component.get("type")
	row = {
		"screen": screen_id,
		"field_type": field_type,
		"field_name": component.get("name", field_type.lower()),
		"label": component.get("label") or component.get("text", ""),
		"required": 1 if component.get("required") else 0,
		"enabled": 1,
		"helper_text": component.get("helper-text", ""),
		"init_value": component.get("init-value", ""),
		"min_chars": component.get("min-chars"),
		"max_chars": component.get("max-chars"),
		"error_message": component.get("error-message", ""),
	}

	if field_type in OPTION_TYPES and component.get("data-source"):
		row["options"] = json.dumps(component["data-source"])

	return row
