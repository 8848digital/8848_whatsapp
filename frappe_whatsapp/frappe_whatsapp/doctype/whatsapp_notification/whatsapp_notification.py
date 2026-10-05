# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2022, Shridhar Patil and contributors
# For license information, please see license.txt

"""WhatsApp Notification: send a template when a document event or schedule fires."""

from frappe.model.document import Document

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification import (
	notification_delivery,
	notification_schedule,
	notification_sender,
)
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_validation import (
	validate_notification,
)
from frappe_whatsapp.frappe_whatsapp.notification_events import clear_notifications_map
from frappe_whatsapp.utils.phone import format_number


class WhatsAppNotification(Document):
	"""Rule for sending a WhatsApp Template on a document event, a date or a schedule."""

	def validate(self):
		"""
		Check the recipients, attachments and fields are set up correctly.

		Returns:
			None
		"""
		validate_notification(self)

	def on_trash(self):
		"""
		Forget the cached event map so the deleted notification stops firing.

		Returns:
			None
		"""
		clear_notifications_map()

	def send_template_message(self, doc, phone_no=None, default_template=None, ignore_condition=False):
		"""
		Send this notification about a document.

		Parameters:
			doc (Document, required): The reference document.
			phone_no (str, optional): Send only to this number.
			default_template (Document | dict, optional): Template to use instead of this one's.
			ignore_condition (bool, optional): Skip the condition check.

		Returns:
			None
		"""
		notification_sender.send_for_document(self, doc, phone_no, default_template, ignore_condition)

	def send_scheduled_message(self):
		"""
		Send this Scheduler Event notification.

		Returns:
			None
		"""
		notification_schedule.send_scheduled(self)

	def send_simple_template(self, template):
		"""
		Send a parameter-less template to every number in self._contact_list.

		Parameters:
			template (dict, required): WhatsApp Templates row.

		Returns:
			None
		"""
		notification_schedule.send_without_document(self, template)

	def get_documents_for_today(self):
		"""
		Send this Days Before / Days After notification for documents due today.

		Returns:
			None
		"""
		notification_schedule.send_for_documents_due_today(self)

	def get_recipients(self, doc, doc_data, phone_no=None):
		"""
		Numbers this notification goes to, as (inline_numbers, role_numbers).

		Parameters:
			doc (Document, required): The reference document.
			doc_data (dict, required): doc.as_dict().
			phone_no (str, optional): Explicit recipient.

		Returns:
			tuple: (list, list)
		"""
		return notification_sender.get_recipients(self, doc, doc_data, phone_no)

	def notify(self, data, doc_data=None):
		"""
		Send one payload and log the result.

		Parameters:
			data (dict, required): Payload with "to" set.
			doc_data (dict, optional): Reference document.

		Returns:
			bool: True when Meta accepted it.
		"""
		return notification_delivery.send_and_log(self, data, doc_data)

	def apply_property_after_alert(self, doc_data):
		"""
		Set the configured field on the reference document.

		Parameters:
			doc_data (dict, required): Reference document with doctype and name.

		Returns:
			None
		"""
		notification_delivery.apply_property_after_alert(self, doc_data)

	def format_number(self, number):
		"""
		Drop a leading "+" from a number; empty values are returned as they are.

		Parameters:
			number (str, optional): Phone number.

		Returns:
			str | None: The number.
		"""
		if not number:
			return number

		return format_number(number)
