# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, Shridhar Patil and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.model.naming import make_autoname

from frappe_whatsapp.frappe_whatsapp.doctype.bulk_whatsapp_message import bulk_progress, bulk_utils


class BulkWhatsAppMessage(Document):
	"""One message (usually a template) sent to many recipients in the background."""

	def autoname(self):
		"""
		Name as BULK-WA-<year>-<number>.

		Returns:
			None
		"""
		self.name = make_autoname("BULK-WA-.YYYY.-.#####")

	def validate(self):
		"""
		Require recipients and count them.

		Returns:
			None
		"""
		bulk_utils.validate_recipients(self)

	def on_submit(self):
		"""
		Queue a background job per recipient.

		Returns:
			None
		"""
		self.db_set("status", "Queued")
		bulk_utils.queue_messages(self)

	def create_single_message(self, recipient):
		"""
		Background job (enqueue_doc): send to one recipient.

		Parameters:
			recipient (dict, required): Recipient row.

		Returns:
			None
		"""
		bulk_utils.create_single_message(self, recipient)

	def retry_failed(self):
		"""
		Queue a re-send of every Failed message.

		Returns:
			None
		"""
		bulk_progress.retry_failed(self)

	def resend_single_message(self, message_name):
		"""
		Background job (enqueue_doc): re-send one Failed message.

		Parameters:
			message_name (str, required): WhatsApp Message name.

		Returns:
			None
		"""
		bulk_progress.resend_single_message(message_name)

	def get_progress(self):
		"""
		Sent / failed / queued counts for the progress bar.

		Returns:
			dict: Progress counts.
		"""
		return bulk_progress.get_progress(self)

	def get_mpm_action_json(self):
		"""
		Multi-Product Message action for this batch, if products are set.

		Returns:
			dict | None: Action JSON.
		"""
		return bulk_utils.get_mpm_action(self)
