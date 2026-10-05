# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, Shridhar Patil and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_profiles.profile_utils import clean_profile


class WhatsAppProfiles(Document):
	"""A WhatsApp contact (number and profile name) seen in messages."""

	def validate(self):
		"""
		Normalize the number and set the title.

		Returns:
			None
		"""
		clean_profile(self)
