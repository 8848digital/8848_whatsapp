# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, 8848 and contributors
# For license information, please see license.txt

"""Turn a print format or a report into a public PDF file for WhatsApp."""

import json

import frappe
from frappe.utils.pdf import get_pdf

REPORT_PDF_OPTIONS = {
	"orientation": "Landscape",
	"page-size": "A4",
	"margin-top": "10mm",
	"margin-bottom": "10mm",
	"margin-left": "10mm",
	"margin-right": "10mm",
}


def generate_file(sender):
	"""
	Build the PDF for a WhatsApp Report Sender and record the result.

	Parameters:
		sender (Document, required): WhatsApp Report Sender.

	Returns:
		str | None: URL of the PDF, or None when it couldn't be made.
	"""
	if sender.format_type == "Print Format":
		file_url = make_print_format_pdf(sender)
	else:
		file_url = make_report_pdf(sender)

	sender.generated_file = file_url or ""
	sender.status = "Success" if file_url else "Failed"

	return file_url


def make_print_format_pdf(sender):
	"""
	PDF of one document in the chosen print format.

	Parameters:
		sender (Document, required): WhatsApp Report Sender with document_doctype, doc_name, print_format.

	Returns:
		str | None: File URL, or None on error (logged).
	"""
	try:
		html = frappe.get_print(
			doctype=sender.document_doctype, name=sender.doc_name, print_format=sender.print_format, as_pdf=False
		)
		return save_public_pdf(f"{sender.doc_name}.pdf", get_pdf(html))
	except Exception:
		frappe.log_error("WhatsApp Print Format Sender", frappe.get_traceback())
		return None


def make_report_pdf(sender):
	"""
	PDF table of a report's rows, run with the sender's filters.

	Parameters:
		sender (Document, required): WhatsApp Report Sender with report and optional filters JSON.

	Returns:
		str | None: File URL, or None on error (logged).
	"""
	try:
		filters = json.loads(sender.filters) if sender.get("filters") else {}
		columns, data = frappe.get_doc("Report", sender.report).get_data(filters=filters, limit=None)

		html = f"<h2>{sender.report}</h2>" + build_report_table(columns, data)
		return save_public_pdf(f"{sender.report}.pdf", get_pdf(html, options=REPORT_PDF_OPTIONS))
	except Exception:
		frappe.log_error("WhatsApp Report Sender", frappe.get_traceback())
		return None


def build_report_table(columns, data):
	"""
	HTML table of report rows.

	Parameters:
		columns (list, required): Report columns (dicts with label/fieldname).
		data (list, required): Rows, as dicts or lists.

	Returns:
		str: HTML table.
	"""
	header_cells = ""
	for column in columns:
		header_cells += f"<th>{column.get('label') or column.get('fieldname')}</th>"

	body_rows = ""
	for row in data:
		if isinstance(row, dict):
			values = [row.get(column.get("fieldname"), "") for column in columns]
		else:
			values = row
		body_rows += "<tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr>"

	return (
		"<table border='1' cellspacing='0' cellpadding='5' width='100%' style='border-collapse: collapse;'>"
		f"<thead><tr>{header_cells}</tr></thead><tbody>{body_rows}</tbody></table>"
	)


def save_public_pdf(file_name, content):
	"""
	Save PDF bytes as a public File so WhatsApp can download it.

	Parameters:
		file_name (str, required): e.g. "SINV-0001.pdf".
		content (bytes, required): PDF content.

	Returns:
		str: File URL.
	"""
	file_doc = frappe.get_doc({"doctype": "File", "file_name": file_name, "content": content, "is_private": 0})
	file_doc.insert(ignore_permissions=True)
	return file_doc.file_url
