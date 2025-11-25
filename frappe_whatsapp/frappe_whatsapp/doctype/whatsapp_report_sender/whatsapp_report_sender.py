# Copyright (c) 2025, 8848 and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf
import json


class WhatsAppReportSender(Document):
	def validate(self):
		if self.format_type == "Print Format":
			file_url = generate_pdf_for_print_format(self)
		else:
			file_url = generate_report_pdf(self)

		if not file_url:
			self.generated_file = ''
			self.status = "Failed"
			
		self.generated_file = file_url
		self.status = "Success"

		return file_url


def generate_pdf_for_print_format(self):
	try:
		html = frappe.get_print(
			doctype=self.document_doctype,
			name=self.doc_name,
			print_format=self.print_format,
			as_pdf=False,
		)

		pdf_bytes = get_pdf(html)

		filename = f"{self.doc_name}.pdf"
		filedoc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": filename,
				"content": pdf_bytes,
				"is_private": 0,
			}
		)
		filedoc.insert(ignore_permissions=True)

		return filedoc.file_url
	except Exception as err:
		return False


def generate_report_pdf(self):
	try:
		if self.get("filters"):
			filters = json.loads(self.filters)
		else:
			filters = {}

		report = frappe.get_doc("Report", self.report)
		columns, data = report.get_data(filters=filters, limit=None)

		html = "<h2>{}</h2>".format(self.report)
		html += """
		<table border='1' cellspacing='0' cellpadding='5' width='100%' style='border-collapse: collapse;'>
			<thead>
				<tr>
		"""

		for col in columns:
			label = col.get("label") or col.get("fieldname")
			html += f"<th>{label}</th>"

		html += "</tr></thead><tbody>"

		for row in data:
			html += "<tr>"
			for col in columns:
				field = col.get("fieldname")
				value = row.get(field, "")
				html += f"<td>{value}</td>"
			html += "</tr>"

		html += "</tbody></table>"
		pdf_options = {
			"orientation": "Landscape",
			"page-size": "A4",
			"margin-top": "10mm",
			"margin-bottom": "10mm",
			"margin-left": "10mm",
			"margin-right": "10mm",
		}

		pdf_data = get_pdf(html, options=pdf_options)

		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"{self.report}.pdf",
				"content": pdf_data,
				"is_private": 0,
			}
		)
		file_doc.insert(ignore_permissions=True)

		return file_doc.file_url
	except Exception as err:
		return False
