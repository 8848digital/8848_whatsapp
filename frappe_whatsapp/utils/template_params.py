# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Clean values before they go into a WhatsApp template."""

import html
import re

from frappe.utils import strip_html_tags

# Meta truncates body parameters beyond this.
MAX_PARAM_LENGTH = 1024


def sanitize_param(value):
	"""
	Flatten a value into something Meta accepts as a template parameter.

	Meta rejects parameters with newlines, tabs or four or more spaces in a
	row, and shows any markup as plain text. Text Editor fields come back
	from get_formatted() wrapped in HTML, so that is stripped first.

	Parameters:
		value (Any, required): Field value to send.

	Returns:
		str: Single-line plain text, at most MAX_PARAM_LENGTH characters.
	"""
	if value is None:
		return ""

	value = html.unescape(strip_html_tags(str(value)))
	value = re.sub(r"\s+", " ", value).strip()

	if len(value) > MAX_PARAM_LENGTH:
		value = value[: MAX_PARAM_LENGTH - 3] + "..."

	return value
