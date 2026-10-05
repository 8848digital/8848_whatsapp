# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""
	Turn on automatic read receipts in WhatsApp Settings (one-time patch).

	Returns:
		None
	"""
	settings = frappe.get_single("WhatsApp Settings")
	settings.allow_auto_read_receipt = 1
	settings.save()
