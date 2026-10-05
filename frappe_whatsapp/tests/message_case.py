# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Shared setup for the WhatsApp Message tests."""

import frappe

from frappe_whatsapp.tests.helpers import IntegrationTestCase, make_test_account, use_test_account


class MessageTestCase(IntegrationTestCase):
    """Default test account, and cleanup of the 9199... test numbers. Has no tests itself."""

    @classmethod
    def setUpClass(cls):
        """Create the shared test records once for the class."""
        super().setUpClass()
        make_test_account("Test WA Msg Account", "msg_test")

    def setUp(self):
        """Make the message test account the default for this test."""
        use_test_account("Test WA Msg Account", "test_token_123")

    def tearDown(self):
        """Delete messages and profiles for the 9199... test numbers."""
        for name in frappe.get_all("WhatsApp Message", filters={"to": ["like", "9199%"]}, pluck="name"):
            frappe.delete_doc("WhatsApp Message", name, force=True)
        for name in frappe.get_all("WhatsApp Message", filters={"from": ["like", "9199%"]}, pluck="name"):
            frappe.delete_doc("WhatsApp Message", name, force=True)
        for name in frappe.get_all("WhatsApp Profiles", filters={"number": ["like", "9199%"]}, pluck="name"):
            frappe.delete_doc("WhatsApp Profiles", name, force=True)
        frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries
