# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Find a flow's screens and fields, and the ${form.x} / ${data.x} references between screens."""


# Components that only display something; they never carry a value.
DISPLAY_TYPES = ("TextHeading", "TextSubheading", "TextBody", "TextCaption", "Image", "EmbeddedLink", "Footer")


def get_field_references(flow, screen_id, source):
	"""
	The screen's input fields, as data declarations or as ${source.field} references.

	Parameters:
		flow (Document, required): WhatsApp Flow.
		screen_id (str, required): Screen id.
		source (str, optional): "form" or "data"; None gives data declarations.

	Returns:
		dict: e.g. {"name": "${form.name}"} or {"name": {"type": "string", "__example__": ""}}
	"""
	references = {}
	for field in get_input_fields(flow, screen_id):
		if source:
			references[field.field_name] = "${" + source + "." + field.field_name + "}"
		else:
			references[field.field_name] = {"type": "string", "__example__": ""}

	return references


def get_next_screen(flow, current_screen):
	"""
	The screen after the current one.

	Parameters:
		flow (Document, required): WhatsApp Flow.
		current_screen (Document, required): Current screen.

	Returns:
		Document | None: Next screen, or None for the last one.
	"""
	screen_ids = [screen.screen_id for screen in flow.screens]
	position = screen_ids.index(current_screen.screen_id)
	if position + 1 < len(flow.screens):
		return flow.screens[position + 1]

	return None


def get_screen_fields(flow, screen_id):
	"""
	Enabled fields on a screen, in table order.

	Parameters:
		flow (Document, required): WhatsApp Flow.
		screen_id (str, required): Screen id.

	Returns:
		list: WhatsApp Flow Field rows.
	"""
	return [field for field in flow.fields if field.screen == screen_id and field.enabled]


def get_input_fields(flow, screen_id):
	"""
	Enabled fields on a screen that collect a value.

	Parameters:
		flow (Document, required): WhatsApp Flow.
		screen_id (str, required): Screen id.

	Returns:
		list: WhatsApp Flow Field rows.
	"""
	return [field for field in get_screen_fields(flow, screen_id) if field.field_type not in DISPLAY_TYPES]
