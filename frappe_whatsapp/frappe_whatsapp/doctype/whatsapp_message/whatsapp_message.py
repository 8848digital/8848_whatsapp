# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2022, Shridhar Patil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message import message_utils
from frappe_whatsapp.utils.phone import format_number


class WhatsAppMessage(Document):
	"""A WhatsApp message sent or received; outgoing ones are sent to Meta when created."""

	def validate(self):
		"""
		Make sure a WhatsApp Account is set.

		Returns:
			None
		"""
		message_utils.set_default_account(self)

	def before_insert(self):
		"""
		Send outgoing messages before they are saved, then create the sender's profile.

		Returns:
			None
		"""
		message_utils.set_default_account(self)
		# message_type is read-only in the form, so picking a template is what makes it a template message.
		if self.template:
			self.message_type = "Template"

		self.send_outgoing()
		message_utils.create_profile(self)

	def on_update(self):
		"""
		Keep the sender's WhatsApp Profile name up to date.

		Returns:
			None
		"""
		message_utils.update_profile_name(self)

	def send_outgoing(self):
		"""
		Send this message to Meta if it is Outgoing (also used by bulk retry).

		Returns:
			None
		"""
		message_utils.send_outgoing(self)

	def send_template(self):
		"""
		Send this message's WhatsApp Template.

		Returns:
			None
		"""
		message_utils.send_template(self)

	def notify(self, data):
		"""
		Post a ready-made payload to Meta for this message.

		Parameters:
			data (dict, required): Meta payload.

		Returns:
			None
		"""
		message_utils.send_payload(self, data)

	def format_number(self, number):
		"""
		Drop a leading "+" from a number.

		Parameters:
			number (str, required): Phone number.

		Returns:
			str: The number without "+".
		"""
		return format_number(number)

	def send_read_receipt(self):
		"""
		Mark this incoming message as read on WhatsApp.

		Returns:
			bool | None: True when Meta accepted it.
		"""
		return message_utils.send_read_receipt(self)


def on_doctype_update():
	"""
	Index the reference columns; chat views look messages up by document.

	Returns:
		None
	"""
	frappe.db.add_index("WhatsApp Message", ["reference_doctype", "reference_name"])
