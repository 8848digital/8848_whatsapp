# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Find a user's phone number on their User or Employee record, per WhatsApp Settings."""

import frappe

# Options of WhatsApp Settings > Phone Number Source.
SOURCE_USER_THEN_EMPLOYEE = "User Mobile No, then Employee"
SOURCE_EMPLOYEE_THEN_USER = "Employee, then User Mobile No"
SOURCE_USER_ONLY = "User Mobile No"
SOURCE_EMPLOYEE_ONLY = "Employee Cell Number"


def get_employee_numbers(users):
	"""
	Employee cell numbers for these users, in one query; empty without HRMS.

	Parameters:
		users (list, required): User names.

	Returns:
		dict: {user: cell_number}
	"""
	if not users or not frappe.db.exists("DocType", "Employee"):
		return {}

	employee_numbers = {}
	for employee in frappe.get_all(
		"Employee",
		filters={"user_id": ("in", list(users))},
		fields=["user_id", "cell_number"],
		ignore_permissions=True,
	):
		employee_numbers[employee.user_id] = employee.cell_number

	return employee_numbers


def resolve_phone(user, source, user_numbers=None, employee_numbers=None):
	"""
	Pick a user's raw phone number following the configured source order.

	Parameters:
		user (str, required): User name.
		source (str, required): One of the SOURCE_* settings values.
		user_numbers (dict, optional): {user: User.mobile_no}
		employee_numbers (dict, optional): {user: Employee.cell_number}

	Returns:
		str | None: The raw number.
	"""
	user_number = (user_numbers or {}).get(user)
	employee_number = (employee_numbers or {}).get(user)

	if source == SOURCE_USER_ONLY:
		return user_number
	if source == SOURCE_EMPLOYEE_ONLY:
		return employee_number
	if source == SOURCE_EMPLOYEE_THEN_USER:
		return employee_number or user_number

	# Default: User first, so the Employee lookup is rarely needed.
	return user_number or employee_number
