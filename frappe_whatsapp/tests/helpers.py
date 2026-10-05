# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Base test class and the WhatsApp Account / Template records the tests share."""

import frappe
from frappe.utils.password import set_encrypted_password

# IntegrationTestCase arrived in Frappe v15; v14 only has FrappeTestCase.
try:
	from frappe.tests import IntegrationTestCase
except ImportError:
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase


def make_test_account(account_name, prefix, token=None, verify_token=None):
	"""
	Create an active, default WhatsApp Account for tests, once.

	Ids are built from the prefix, e.g. prefix "msg_test" gives phone_id
	"msg_test_phone_id", which tests use to match webhook payloads.

	Parameters:
		account_name (str, required): Account name, e.g. "Test WA Msg Account".
		prefix (str, required): Prefix for phone_id, business_id, app_id and verify token.
		token (str, optional): Access token to store; tests that hit get_password need one.
		verify_token (str, optional): Webhook verify token; defaults to "<prefix>_verify_token".

	Returns:
		None
	"""
	if frappe.db.exists("WhatsApp Account", account_name):
		return

	account = frappe.get_doc(
		{
			"doctype": "WhatsApp Account",
			"account_name": account_name,
			"status": "Active",
			"url": "https://graph.facebook.com",
			"version": "v17.0",
			"phone_id": f"{prefix}_phone_id",
			"business_id": f"{prefix}_business_id",
			"app_id": f"{prefix}_app_id",
			"webhook_verify_token": verify_token or f"{prefix}_verify_token",
			"is_default_incoming": 1,
			"is_default_outgoing": 1,
		}
	)
	account.insert(ignore_permissions=True)

	if token:
		set_encrypted_password("WhatsApp Account", account.name, token, "token")

	frappe.db.commit()  # nosemgrep: frappe-manual-commit -- shared fixture must survive per-test rollbacks


def make_test_template(template_name, account_name, body, sample_values, category="MARKETING", **fields):
	"""
	Insert an APPROVED WhatsApp Template for tests, once, without its hooks.

	Hooks are skipped because saving normally creates the template on Meta.

	Parameters:
		template_name (str, required): Template name; the record is named "<template_name>-en".
		account_name (str, required): WhatsApp Account it belongs to.
		body (str, required): Template text, e.g. "Hello {{1}}".
		sample_values (str, required): Comma separated samples for the placeholders.
		category (str, optional): Meta category. Defaults to "MARKETING".
		fields (dict, optional): Any other WhatsApp Templates fields.

	Returns:
		None
	"""
	if frappe.db.exists("WhatsApp Templates", f"{template_name}-en"):
		return

	template = frappe.get_doc(
		{
			"doctype": "WhatsApp Templates",
			"template_name": template_name,
			"actual_name": template_name,
			"template": body,
			"sample_values": sample_values,
			"category": category,
			"language": frappe.db.get_value("Language", {"language_code": "en"}) or "en",
			"language_code": "en",
			"whatsapp_account": account_name,
			"status": "APPROVED",
			"id": f"{template_name}_id",
			**fields,
		}
	)
	template.db_insert()
	frappe.db.commit()  # nosemgrep: frappe-manual-commit -- shared fixture must survive per-test rollbacks


def use_test_account(account_name, token=None):
	"""
	Make a test account the only default (and set its token), for one test.

	Runs in setUp because each test's transaction is rolled back afterwards.
	db.set_value is used so WhatsApp Account's on_update hooks don't run.

	Parameters:
		account_name (str, required): WhatsApp Account name.
		token (str, optional): Access token to store on it.

	Returns:
		None
	"""
	if token:
		set_encrypted_password("WhatsApp Account", account_name, token, "token")

	frappe.db.sql("UPDATE `tabWhatsApp Account` SET is_default_outgoing=0, is_default_incoming=0")
	frappe.db.set_value(
		"WhatsApp Account", account_name, {"is_default_outgoing": 1, "is_default_incoming": 1}
	)
