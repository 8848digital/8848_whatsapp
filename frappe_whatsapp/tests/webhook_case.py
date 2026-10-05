# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Shared setup for the webhook endpoint tests."""

from unittest.mock import MagicMock

import frappe

from frappe_whatsapp.tests.helpers import IntegrationTestCase, make_test_account, use_test_account


class WebhookEndpointTestCase(IntegrationTestCase):
    """Default account for webhook calls, cleaned up after every test. Has no tests itself."""

    @classmethod
    def setUpClass(cls):
        """Create the shared test records once for the class."""
        super().setUpClass()
        make_test_account(
            "Test WA Webhook EP Account", "webhook_ep", token="ep_token", verify_token="Test WA Webhook EP Account"
        )

    def setUp(self):
        """Make the webhook test account the default for this test."""
        use_test_account("Test WA Webhook EP Account", "ep_token")

    def tearDown(self):
        """Delete the messages, logs and profiles the webhook calls created."""
        for name in frappe.get_all("WhatsApp Message", filters={"message_id": ["like", "wamid.webhook_ep_%"]}, pluck="name"):
            frappe.delete_doc("WhatsApp Message", name, force=True)
        for name in frappe.get_all("WhatsApp Notification Log", filters={"template": "Webhook"}, pluck="name"):
            frappe.delete_doc("WhatsApp Notification Log", name, force=True)
        for name in frappe.get_all("WhatsApp Profiles", filters={"number": ["like", "9199%"]}, pluck="name"):
            frappe.delete_doc("WhatsApp Profiles", name, force=True)
        frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

    def _make_mock_request(self, method="GET"):
        """Create a mock request object."""
        mock_request = MagicMock()
        mock_request.method = method
        return mock_request
