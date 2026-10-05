# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, Shridhar Patil and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_account.account_utils import (
	keep_single_default,
	subscribe_app_to_webhooks,
)


class WhatsAppAccount(Document):
	"""A WhatsApp Business phone number and the Meta credentials used to send from it."""

	def on_update(self):
		"""
		Only one account can be the default incoming and one the default outgoing.

		Returns:
			None
		"""
		keep_single_default(self)

	def subscribe_app(self):
		"""
		Subscribe the Meta app to this account's webhooks.

		Returns:
			dict: Meta's response.
		"""
		return subscribe_app_to_webhooks(self)
