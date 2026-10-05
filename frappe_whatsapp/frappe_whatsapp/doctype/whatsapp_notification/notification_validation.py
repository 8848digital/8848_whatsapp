# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Checks run when a WhatsApp Notification is saved."""

import frappe
from frappe import _


def validate_notification(notification):
	"""
	Run every check on a WhatsApp Notification before it is saved.

	Parameters:
		notification (Document, required): The WhatsApp Notification.

	Returns:
		None
	"""
	if notification.notification_type == "DocType Event":
		validate_recipient_source(notification)

	warn_child_table_fields(notification)
	validate_role_attachments(notification)
	validate_custom_attachment(notification)
	validate_property_after_alert(notification)


def validate_recipient_source(notification):
	"""
	A DocType Event notification needs a phone number field or at least one role.

	Parameters:
		notification (Document, required): The WhatsApp Notification.

	Returns:
		None
	"""
	if not notification.field_name:
		if not notification.get("recipients"):
			frappe.throw(
				_("Set a {0} or add at least one role under {1}").format(
					frappe.bold(_("Field Name (Phone Number)")),
					frappe.bold(_("Recipients by Role")),
				)
			)
		return

	fieldnames = set()
	for field in frappe.get_doc("DocType", notification.reference_doctype).fields:
		fieldnames.add(field.fieldname)
	custom_fields = frappe.get_all(
		"Custom Field", filters={"dt": notification.reference_doctype}, pluck="fieldname"
	)
	fieldnames.update(custom_fields)

	if notification.field_name not in fieldnames:
		frappe.throw(_("Field name {0} does not exists").format(notification.field_name))


def warn_child_table_fields(notification):
	"""
	Warn about "fieldname,parentfield" parameters, which always send an empty value.

	Parameters:
		notification (Document, required): The WhatsApp Notification.

	Returns:
		None
	"""
	for field in notification.fields:
		if "," not in (field.field_name or ""):
			continue

		frappe.msgprint(
			_(
				"Child table field {0} is not supported and will send an empty value. "
				"Set Reference Document Type to the child doctype instead."
			).format(frappe.bold(field.field_name)),
			indicator="orange",
			alert=True,
		)


def validate_role_attachments(notification):
	"""
	Role recipients can't get attachments: the same private-file link would go to everyone in the role.

	Parameters:
		notification (Document, required): The WhatsApp Notification.

	Returns:
		None
	"""
	if not notification.get("recipients"):
		return

	if notification.custom_attachment or notification.attach_document_print:
		frappe.throw(
			_(
				"Recipients by Role cannot be combined with {0} or {1}: the same "
				"private-file link would be sent to everyone holding the role."
			).format(frappe.bold(_("Custom Attachment")), frappe.bold(_("Attach Document Print")))
		)


def validate_custom_attachment(notification):
	"""
	A custom attachment needs either an attached file or a field to take it from.

	Parameters:
		notification (Document, required): The WhatsApp Notification.

	Returns:
		None
	"""
	if notification.custom_attachment and not notification.attach and not notification.attach_from_field:
		frappe.throw(
			_("Either {0} a file or add a {1} to send attachemt").format(
				frappe.bold(_("Attach")), frappe.bold(_("Attach from field"))
			)
		)


def validate_property_after_alert(notification):
	"""
	The field to set after sending must exist on the reference DocType.

	Parameters:
		notification (Document, required): The WhatsApp Notification.

	Returns:
		None
	"""
	if not notification.set_property_after_alert:
		return

	meta = frappe.get_meta(notification.reference_doctype)
	if not meta.get_field(notification.set_property_after_alert):
		frappe.throw(
			_("Field {0} not found on DocType {1}").format(
				notification.set_property_after_alert, notification.reference_doctype
			)
		)
