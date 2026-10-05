# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""
Turn a WhatsApp Notification's "Recipients by Role" rows into phone numbers.

Used by all three send paths: DocType events, date-based events
(Days Before/After) and Scheduler events.
"""

import frappe
from frappe.utils.safe_exec import get_safe_globals

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.recipient_phone import (
	SOURCE_USER_ONLY,
	SOURCE_USER_THEN_EMPLOYEE,
	get_employee_numbers,
	resolve_phone,
)
from frappe_whatsapp.utils.phone import normalize_number

# Never notify the built-in accounts, matching what core Frappe's
# get_info_based_on_role does for the Email channel.
EXCLUDED_USERS = ("Administrator", "Guest")


def get_role_recipients(notification, doc=None):
	"""
	Resolve the notification's role rows into people to message.

	Someone holding two matching roles is messaged once: recipients are
	de-duplicated on the normalized number.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		doc (Document, optional): Reference document for row conditions; None for scheduler events.

	Returns:
		tuple: (recipients [{"user", "full_name", "phone"}], skipped [{"user", "reason"}])
	"""
	if not notification.get("recipients"):
		return [], []

	users = get_users_for_roles(get_matching_roles(notification, doc))
	if not users:
		return [], []

	settings = frappe.get_cached_doc("WhatsApp Settings")
	source = settings.get("role_phone_source") or SOURCE_USER_THEN_EMPLOYEE
	country_code = settings.get("default_country_code")

	user_details = {}
	for user_row in frappe.get_all(
		"User",
		filters={"name": ("in", users)},
		fields=["name", "full_name", "mobile_no"],
		ignore_permissions=True,
	):
		user_details[user_row.name] = user_row

	user_numbers = {name: details.mobile_no for name, details in user_details.items()}
	employee_numbers = get_employee_numbers(users) if source != SOURCE_USER_ONLY else {}

	recipients = []
	skipped = []
	seen_numbers = set()
	for user in users:
		raw_number = resolve_phone(user, source, user_numbers, employee_numbers)
		if not raw_number:
			skipped.append({"user": user, "reason": "no phone number"})
			continue

		phone = normalize_number(raw_number, country_code)
		if not phone:
			skipped.append({"user": user, "reason": f"unusable number: {raw_number}"})
			continue

		# "+91..." and "91..." are the same person once normalized.
		if phone in seen_numbers:
			continue
		seen_numbers.add(phone)

		details = user_details.get(user) or {}
		recipients.append({"user": user, "full_name": details.get("full_name") or user, "phone": phone})

	return recipients, skipped


def get_matching_roles(notification, doc=None):
	"""
	Roles whose row condition passes for this document.

	Rows with a condition are skipped for scheduler events, which have no
	document to check it against. A broken condition is logged and skipped.

	Parameters:
		notification (Document, required): The WhatsApp Notification.
		doc (Document, optional): Reference document.

	Returns:
		list: Role names.
	"""
	roles = []
	for row in notification.recipients:
		if not row.receiver_by_role:
			continue

		if row.condition and not condition_passes(notification, row, doc):
			continue

		roles.append(row.receiver_by_role)

	return roles


def condition_passes(notification, row, doc):
	"""
	Evaluate one role row's condition against the document.

	Parameters:
		notification (Document, required): The WhatsApp Notification (for the error log).
		row (Document, required): WhatsApp Notification Recipient row with a condition.
		doc (Document, optional): Reference document.

	Returns:
		bool: True when the condition is met.
	"""
	if doc is None:
		return False

	try:
		return bool(frappe.safe_eval(row.condition, get_safe_globals(), {"doc": doc.as_dict()}))
	except Exception:
		frappe.log_error(
			title="WhatsApp Notification: recipient condition failed",
			message=(
				f"Notification: {notification.name}\n"
				f"Role: {row.receiver_by_role}\n"
				f"Condition: {row.condition}\n\n"
				f"{frappe.get_traceback()}"
			),
		)
		return False


def get_users_for_roles(roles):
	"""
	Enabled users holding any of these roles, in one query for all roles.

	Parameters:
		roles (list, required): Role names.

	Returns:
		list: Sorted user names.
	"""
	if not roles:
		return []

	users = frappe.get_all(
		"Has Role",
		# "Has Role" is also a child of Role Profile; this keeps only users.
		filters={"role": ("in", list(roles)), "parenttype": "User"},
		pluck="parent",
		ignore_permissions=True,
	)

	candidates = set(users) - set(EXCLUDED_USERS)
	if not candidates:
		return []

	enabled_users = frappe.get_all(
		"User",
		filters={"name": ("in", list(candidates)), "enabled": 1},
		pluck="name",
		ignore_permissions=True,
	)

	return sorted(enabled_users)


def log_skipped(notification_name, skipped):
	"""
	Log users without a usable number, once per run rather than once per user.

	Parameters:
		notification_name (str, required): WhatsApp Notification name.
		skipped (list, required): [{"user", "reason"}]

	Returns:
		None
	"""
	if not skipped:
		return

	lines = "\n".join(f"{entry['user']}: {entry['reason']}" for entry in skipped)
	frappe.log_error(
		title="WhatsApp Notification: recipients skipped",
		message=(
			f"Notification: {notification_name}\n"
			f"{len(skipped)} recipient(s) had no usable WhatsApp number.\n\n{lines}"
		),
	)
