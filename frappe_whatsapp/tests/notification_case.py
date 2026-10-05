# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Shared setup for the WhatsApp Notification tests."""

import frappe

from frappe_whatsapp.tests.helpers import IntegrationTestCase, make_test_account, make_test_template, use_test_account


class NotificationTestCase(IntegrationTestCase):
    """Test account, template and a notification factory. Has no tests itself."""

    @classmethod
    def setUpClass(cls):
        """Create the shared test records once for the class."""
        super().setUpClass()
        make_test_account("Test WA Notif Account", "notif_test")
        make_test_template(
            "test_notif_template", "Test WA Notif Account", "Hello {{1}}, your order {{2}} is ready",
            "John,ORD-001", category="TRANSACTIONAL", header_type="",
        )

    def setUp(self):
        """Make the notification test account the default for this test."""
        use_test_account("Test WA Notif Account", "test_notif_token")

    def tearDown(self):
        """Delete the "Test Notif..." notifications."""
        for name in frappe.get_all("WhatsApp Notification", filters={"notification_name": ["like", "Test Notif%"]}, pluck="name"):
            frappe.delete_doc("WhatsApp Notification", name, force=True)
        frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

    def _make_notification(self, **kwargs):
        """
        Insert a WhatsApp Notification for User, overriding any field through kwargs.

        Parameters:
            kwargs (dict, optional): Field values, plus "fields" and "roles" lists.

        Returns:
            Document: The saved WhatsApp Notification.
        """
        doc = frappe.get_doc({
            "doctype": "WhatsApp Notification",
            "notification_name": kwargs.get("notification_name", "Test Notif 1"),
            "notification_type": kwargs.get("notification_type", "DocType Event"),
            "reference_doctype": kwargs.get("reference_doctype", "User"),
            "field_name": kwargs.get("field_name", "mobile_no"),
            "doctype_event": kwargs.get("doctype_event", "After Save"),
            "template": kwargs.get("template", "test_notif_template-en"),
            "disabled": kwargs.get("disabled", 0),
            "condition": kwargs.get("condition", ""),
        })
        if kwargs.get("fields"):
            for f in kwargs["fields"]:
                doc.append("fields", {"field_name": f})
        for role in kwargs.get("roles", []):
            doc.append("recipients", {"receiver_by_role": role})
        doc.insert(ignore_permissions=True)
        return doc
