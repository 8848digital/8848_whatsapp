# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2022, Shridhar Patil and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_media import upload_sample_media
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_meta import (
	create_template_on_meta,
	delete_template_on_meta,
	update_template_on_meta,
)
from frappe_whatsapp.utils.meta_api import get_whatsapp_account


class WhatsAppTemplates(Document):
	"""A WhatsApp message template, kept in sync with Meta."""

	def validate(self):
		"""
		Fill defaults, upload a sample media header and push edits to Meta.

		Approved templates are not pushed: Meta doesn't allow editing them and answers 400.

		Returns:
			None
		"""
		self.set_whatsapp_account()
		self.set_language_code()

		if self.header_type in ("IMAGE", "DOCUMENT") and self.sample:
			upload_sample_media(self)

		if not self.is_new() and self.status != "APPROVED":
			update_template_on_meta(self)

	def after_insert(self):
		"""
		Submit the new template to Meta for approval.

		Returns:
			None
		"""
		create_template_on_meta(self)

	def on_trash(self):
		"""
		Delete the template on Meta too.

		Returns:
			None
		"""
		delete_template_on_meta(self)

	def set_whatsapp_account(self):
		"""
		Use the default WhatsApp Account when none is chosen.

		Returns:
			None
		"""
		if self.whatsapp_account:
			return

		default_account = get_whatsapp_account()
		if not default_account:
			frappe.throw(_("Please set a default outgoing WhatsApp Account or Select available WhatsApp Account"))

		self.whatsapp_account = default_account.name

	def set_language_code(self):
		"""
		Set Meta's language code from the Language, e.g. "en-US" -> "en_US".

		Returns:
			None
		"""
		if self.language_code and not self.has_value_changed("language"):
			return

		language_code = frappe.db.get_value("Language", self.language) or "en"
		self.language_code = language_code.replace("-", "_")
