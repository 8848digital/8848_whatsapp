# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Check recipients, then queue and send the messages of a Bulk WhatsApp Message."""

import json

import frappe
from frappe import _
from frappe.utils import cint

# Meta's limit for products in one Multi-Product Message.
MAX_MPM_PRODUCTS = 30


def validate_recipients(bulk_message):
	"""
	Require recipients and store how many there are.

	Parameters:
		bulk_message (Document, required): Bulk WhatsApp Message.

	Returns:
		None
	"""
	if not bulk_message.recipients and not bulk_message.recipient_list:
		frappe.throw(_("At least one recipient or a recipient list is required"))

	if bulk_message.recipient_type == "Recipient List" and bulk_message.recipient_list:
		recipient_count = frappe.db.count("WhatsApp Recipient", {"parent": bulk_message.recipient_list})
		if recipient_count == 0:
			frappe.throw(_("Selected recipient list has no recipients"))
		bulk_message.recipient_count = recipient_count
	elif bulk_message.recipients:
		bulk_message.recipient_count = len(bulk_message.recipients)


def queue_messages(bulk_message):
	"""
	Queue one background job per recipient on the long queue.

	Parameters:
		bulk_message (Document, required): Submitted Bulk WhatsApp Message.

	Returns:
		None
	"""
	if bulk_message.recipient_type == "Recipient List" and bulk_message.recipient_list:
		recipients = frappe.get_all(
			"WhatsApp Recipient",
			filters={"parent": bulk_message.recipient_list},
			fields=["mobile_number", "name", "recipient_name", "recipient_data"],
		)
	else:
		recipients = bulk_message.recipients

	for recipient in recipients:
		frappe.enqueue_doc(
			bulk_message.doctype, bulk_message.name, "create_single_message", "long", 4000, recipient=recipient
		)


def create_single_message(bulk_message, recipient):
	"""
	Create (and so send) the WhatsApp Message for one recipient.

	A failed insert marks the batch Partially Failed; the attempt is still counted.

	Parameters:
		bulk_message (Document, required): Bulk WhatsApp Message.
		recipient (dict, required): Row with mobile_number and optional recipient_data JSON.

	Returns:
		None
	"""
	recipient_data = recipient.get("recipient_data")

	message = frappe.new_doc("WhatsApp Message")
	message.to = recipient.get("mobile_number")
	message.message_type = "Text"
	message.flags.custom_ref_doc = parse_recipient_data(recipient_data)
	message.bulk_message_reference = bulk_message.name
	if bulk_message.whatsapp_account:
		message.whatsapp_account = bulk_message.whatsapp_account

	if bulk_message.use_template:
		set_template_values(bulk_message, message, recipient_data)

	message.status = "Queued"
	try:
		message.insert(ignore_permissions=True)
	except Exception:
		bulk_message.db_set("status", "Partially Failed")

	bulk_message.db_set("sent_count", cint(bulk_message.sent_count) + 1)
	if bulk_message.recipient_count == bulk_message.sent_count:
		bulk_message.db_set("status", "Completed")


def set_template_values(bulk_message, message, recipient_data):
	"""
	Fill in the template, its variables, attachment and product list on the message.

	Parameters:
		bulk_message (Document, required): Bulk WhatsApp Message using a template.
		message (Document, required): New WhatsApp Message.
		recipient_data (str, optional): Recipient's variables as JSON.

	Returns:
		None
	"""
	message.template = bulk_message.template
	message.message_type = "Template"
	message.use_template = bulk_message.use_template

	mpm_action = get_mpm_action(bulk_message)
	if mpm_action:
		message.product_catalog_json = json.dumps(mpm_action)

	if recipient_data and bulk_message.variable_type == "Unique":
		message.body_param = recipient_data
	elif bulk_message.template_variables and bulk_message.variable_type == "Common":
		message.body_param = bulk_message.template_variables

	if bulk_message.attach:
		message.attach = bulk_message.attach


def parse_recipient_data(recipient_data):
	"""
	Recipient variables as a dict; bad JSON is logged and treated as empty.

	Parameters:
		recipient_data (str, optional): JSON text.

	Returns:
		dict: Variables.
	"""
	try:
		return json.loads(recipient_data or "{}")
	except Exception as e:
		frappe.log_error(f"Error parsing recipient data: {str(e)}", "WhatsApp Bulk Messaging")
		return {}


def get_mpm_action(bulk_message):
	"""
	Multi-Product Message "action" built from the product ids typed on the batch.

	Parameters:
		bulk_message (Document, required): Bulk WhatsApp Message.

	Returns:
		dict | None: Action JSON, or None when products aren't set up.
	"""
	if not bulk_message.whatsapp_account or not bulk_message.thumbnail_product_retailer_id or not bulk_message.product_ids:
		return None

	product_ids = []
	for product_id in bulk_message.product_ids.split(","):
		product_id = product_id.strip()
		if product_id and product_id not in product_ids:
			product_ids.append(product_id)

	if len(product_ids) > MAX_MPM_PRODUCTS:
		product_ids = product_ids[:MAX_MPM_PRODUCTS]
		frappe.msgprint(
			_("Note: Only the first 30 products were included due to WhatsApp limitations."), indicator="orange"
		)

	return {
		"thumbnail_product_retailer_id": bulk_message.thumbnail_product_retailer_id,
		"sections": [
			{
				"title": bulk_message.mpm_header or "Our Products",
				"product_items": [{"product_retailer_id": product_id} for product_id in product_ids],
			}
		],
	}
