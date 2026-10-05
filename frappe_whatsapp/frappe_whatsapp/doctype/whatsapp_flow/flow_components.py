# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Input components (text, choices, opt-in) of a WhatsApp Flow screen."""

import json

OPTION_TYPES = ("Dropdown", "RadioButtonsGroup", "CheckboxGroup")


def build_input_component(field):
	"""
	An input component (text, choice, opt-in...) with its validation settings.

	Parameters:
		field (Document, required): WhatsApp Flow Field row.

	Returns:
		dict: Component.
	"""
	field_type = field.field_type
	component = {"type": field_type, "name": field.field_name, "label": field.label or field.field_name}

	if field.required:
		component["required"] = True
	if field.helper_text:
		component["helper-text"] = field.helper_text
	if field.init_value:
		component["init-value"] = field.init_value

	if field_type in ("TextInput", "TextArea"):
		if field.min_chars:
			component["min-chars"] = field.min_chars
		if field.max_chars:
			component["max-chars"] = field.max_chars
		if field.error_message:
			component["error-message"] = field.error_message

	if field_type in OPTION_TYPES:
		options = parse_options(field.options)
		if options:
			component["data-source"] = options

	if field_type == "OptIn":
		component["label"] = field.label or "I agree"

	return component


def parse_options(options_json):
	"""
	Options for a dropdown/radio/checkbox field from its JSON text.

	Parameters:
		options_json (str, optional): e.g. '[{"id": "a", "title": "A"}]'

	Returns:
		list: Options, or [] when empty or invalid.
	"""
	if not options_json:
		return []

	try:
		options = json.loads(options_json)
	except json.JSONDecodeError:
		return []

	return options if isinstance(options, list) else []
