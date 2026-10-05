# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, 8848 and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_report_sender.report_pdf import generate_file


class WhatsAppReportSender(Document):
	"""Builds a PDF of a print format or report to send over WhatsApp."""

	def validate(self):
		"""
		Generate the PDF and set Generated File and Status.

		Returns:
			str | None: URL of the PDF.
		"""
		return generate_file(self)
