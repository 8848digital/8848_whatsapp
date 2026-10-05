# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, Shridhar Patil and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_recipient_list.recipient_import import import_recipients


class WhatsAppRecipientList(Document):
	"""A saved list of phone numbers (with per-recipient variables) for bulk messages."""

	def validate(self):
		"""
		A saved list must keep at least one recipient.

		Returns:
			None
		"""
		if not self.is_new() and not self.recipients:
			frappe.throw(_("At least one recipient is required"))

	def import_list_from_doctype(
		self, doctype, mobile_field, name_field=None, filters=None, limit=None, data_fields=None
	):
		"""
		Replace the recipients with records of another DocType.

		Parameters:
			doctype (str, required): DocType to read recipients from.
			mobile_field (str, required): Field holding the mobile number.
			name_field (str, optional): Field holding the recipient's name.
			filters (dict, optional): Filters for the records.
			limit (int, optional): Maximum records to import.
			data_fields (list, optional): Fields kept as template variables.

		Returns:
			int: Number of recipients added.
		"""
		return import_recipients(self, doctype, mobile_field, name_field, filters, limit, data_fields)
