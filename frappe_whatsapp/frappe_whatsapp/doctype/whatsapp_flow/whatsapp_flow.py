# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, Shridhar Patil and contributors
# For license information, please see license.txt

import json

from frappe.model.document import Document

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow import flow_meta, flow_status
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_builder import generate_flow_json, validate_screens


class WhatsAppFlow(Document):
	"""A WhatsApp Flow (in-chat form) built from screens and fields, and managed on Meta."""

	def validate(self):
		"""
		Check the screens are set up correctly.

		Returns:
			None
		"""
		validate_screens(self)

	def before_save(self):
		"""
		Keep the stored Flow JSON in step with the screens and fields.

		Returns:
			None
		"""
		self.flow_json = json.dumps(self.generate_flow_json(), indent=2)

	def generate_flow_json(self):
		"""
		Build WhatsApp's Flow JSON for this flow.

		Returns:
			dict: Flow JSON.
		"""
		return generate_flow_json(self)

	def create_on_whatsapp(self):
		"""
		Create this flow on WhatsApp and upload its JSON.

		Returns:
			None
		"""
		flow_meta.create_flow_on_meta(self)

	def upload_flow_json(self):
		"""
		Upload the current Flow JSON to WhatsApp.

		Returns:
			None
		"""
		flow_meta.upload_flow_json(self)

	def publish_flow(self):
		"""
		Publish this flow on WhatsApp.

		Returns:
			None
		"""
		flow_meta.publish_flow(self)

	def deprecate_flow(self):
		"""
		Deprecate this flow on WhatsApp.

		Returns:
			None
		"""
		flow_meta.deprecate_flow(self)

	def delete_from_whatsapp(self):
		"""
		Delete this flow on WhatsApp.

		Returns:
			None
		"""
		flow_meta.delete_flow_on_meta(self)

	def get_flow_preview(self):
		"""
		Get the web preview link.

		Returns:
			str: Preview URL.
		"""
		return flow_status.get_preview_url(self)

	def send_test(self, phone_number, message=None):
		"""
		Send this flow to a phone number to try it.

		Parameters:
			phone_number (str, required): Recipient number.
			message (str, optional): Message text.

		Returns:
			str: WhatsApp Message name.
		"""
		return flow_meta.send_test_flow(self, phone_number, message)

	def get_flow_status(self):
		"""
		Read status and validation errors from WhatsApp.

		Returns:
			dict: Flow details from Meta.
		"""
		return flow_status.get_flow_status(self)

	def sync_from_whatsapp(self):
		"""
		Copy details and Flow JSON from WhatsApp.

		Returns:
			dict: Flow details from Meta.
		"""
		return flow_status.sync_flow_from_meta(self)
