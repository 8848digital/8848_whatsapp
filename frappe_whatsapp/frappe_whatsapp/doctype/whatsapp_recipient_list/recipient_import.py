# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Fill a WhatsApp Recipient List from the records of another DocType."""

import json

import frappe
from frappe.model import default_fields


def import_into_list(list_name, doctype, mobile_field, name_field=None, filters=None, limit=None, data_fields=None):
	"""
	Load a recipient list the user can edit, import into it and save.

	Parameters:
		list_name (str, required): WhatsApp Recipient List name.
		doctype (str, required): DocType to read recipients from, e.g. "Customer".
		mobile_field (str, required): Field holding the mobile number.
		name_field (str, optional): Field holding the recipient's name.
		filters (dict | str, optional): Filters, as a dict or JSON text.
		limit (int, optional): Maximum records to import.
		data_fields (list | str, optional): Fields kept as template variables, as a list or JSON text.

	Returns:
		int: Number of recipients now in the list.
	"""
	if filters and isinstance(filters, str):
		filters = json.loads(filters)
	if data_fields and isinstance(data_fields, str):
		data_fields = json.loads(data_fields)

	recipient_list = frappe.get_doc("WhatsApp Recipient List", list_name)
	recipient_list.check_permission("write")

	count = recipient_list.import_list_from_doctype(doctype, mobile_field, name_field, filters, limit, data_fields)
	recipient_list.save()

	return count


def import_recipients(recipient_list, doctype, mobile_field, name_field=None, filters=None, limit=None, data_fields=None):
	"""
	Replace the list's recipients with records of a DocType that have a mobile number.

	Numbers are cleaned to digits and "+". Each data field is stored per
	recipient (as recipient_data JSON) for use as a template variable.

	Parameters:
		recipient_list (Document, required): WhatsApp Recipient List.
		doctype (str, required): DocType to read recipients from.
		mobile_field (str, required): Field holding the mobile number.
		name_field (str, optional): Field holding the recipient's name.
		filters (dict, optional): Filters for the records.
		limit (int, optional): Maximum records to import.
		data_fields (list, optional): Fields kept as template variables.

	Returns:
		int: Number of recipients added.
	"""
	recipient_list.doctype_to_import = doctype
	recipient_list.mobile_field = mobile_field
	recipient_list.filters = filters
	if data_fields:
		recipient_list.data_fields = json.dumps(data_fields)
	if limit:
		recipient_list.import_limit = limit

	records = frappe.get_all(
		doctype, filters=filters, fields=get_fields_to_read(doctype, mobile_field, name_field, data_fields), limit=limit
	)

	recipient_list.recipients = []
	for record in records:
		mobile = clean_mobile(record.get(mobile_field))
		if not mobile:
			continue

		recipient = {"mobile_number": mobile, "recipient_data": json.dumps(get_recipient_data(record, data_fields))}
		if name_field and record.get(name_field):
			recipient["recipient_name"] = record.get(name_field)

		recipient_list.append("recipients", recipient)

	return len(recipient_list.recipients)


def get_fields_to_read(doctype, mobile_field, name_field=None, data_fields=None):
	"""
	Fields to fetch: mobile, name, and the data fields that exist on the DocType.

	Parameters:
		doctype (str, required): DocType being read.
		mobile_field (str, required): Mobile number field.
		name_field (str, optional): Name field.
		data_fields (list, optional): Template variable fields.

	Returns:
		list: Field names.
	"""
	fields = [mobile_field]
	if name_field:
		fields.append(name_field)
	if not data_fields:
		return fields

	valid_fieldnames = {field.fieldname for field in frappe.get_meta(doctype).fields}
	for field in data_fields:
		if field not in fields and (field in valid_fieldnames or field in default_fields):
			fields.append(field)

	return fields


def get_recipient_data(record, data_fields=None):
	"""
	The record's non-empty data fields, keyed as template variables ("Due Date" -> "due_date").

	Parameters:
		record (dict, required): Record being imported.
		data_fields (list, optional): Template variable fields.

	Returns:
		dict: Variables for this recipient.
	"""
	recipient_data = {}
	for field in data_fields or []:
		if record.get(field):
			recipient_data[field.lower().replace(" ", "_")] = record.get(field)

	return recipient_data


def clean_mobile(mobile):
	"""
	Keep only digits and "+" in a mobile number, e.g. "+91 98765-43210" -> "+919876543210".

	Parameters:
		mobile (str, optional): Mobile number as stored.

	Returns:
		str: Cleaned number, or "" when there is none.
	"""
	if not mobile:
		return ""

	return "".join(char for char in mobile if char.isdigit() or char == "+")
