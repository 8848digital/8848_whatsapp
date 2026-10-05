# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Status helpers the webhook uses: message delivery and template approval updates."""

import frappe

from frappe_whatsapp.tests.helpers import IntegrationTestCase, make_test_account
from frappe_whatsapp.utils.webhook import (
    update_message_status,
    update_status,
    update_template_status,
)


class TestWebhookHelpers(IntegrationTestCase):
    """Tests for webhook helper functions."""

    @classmethod
    def setUpClass(cls):
        """Create the shared test records once for the class."""
        super().setUpClass()
        make_test_account("Test WA Webhook Account", "webhook_test", token="test_webhook_token")

    def setUp(self):
        # Set password within each test's transaction scope
        """Give the webhook test account its token for this test."""
        from frappe.utils.password import set_encrypted_password
        set_encrypted_password("WhatsApp Account", "Test WA Webhook Account", "test_webhook_token", "token")

    def tearDown(self):
        """Delete the messages and logs this test created."""
        for name in frappe.get_all("WhatsApp Message", filters={"message_id": ["like", "wamid.webhook_%"]}, pluck="name"):
            frappe.delete_doc("WhatsApp Message", name, force=True)
        for name in frappe.get_all("WhatsApp Notification Log", filters={"template": "Webhook"}, pluck="name"):
            frappe.delete_doc("WhatsApp Notification Log", name, force=True)
        frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

    def test_update_status_template_status(self):
        """Test update_status routes to template status update."""
        data = {
            "field": "message_template_status_update",
            "value": {
                "event": "APPROVED",
                "message_template_id": "999999",
            }
        }
        # Should not raise
        update_status(data)

    def test_update_message_status(self):
        """Test update_message_status updates WhatsApp Message status."""
        # Create a message first
        msg = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": "919900112233",
            "message": "Status test",
            "message_id": "wamid.webhook_status_test",
            "content_type": "text",
            "whatsapp_account": "Test WA Webhook Account",
        })
        msg.flags.ignore_validate = True
        msg.db_insert()
        frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

        data = {
            "statuses": [{
                "id": "wamid.webhook_status_test",
                "status": "delivered",
                "conversation": {"id": "conv_123"}
            }]
        }
        update_message_status(data)

        msg.reload()
        self.assertEqual(msg.status, "delivered")
        self.assertEqual(msg.conversation_id, "conv_123")

    def test_update_message_status_without_conversation(self):
        """Test update_message_status when no conversation ID."""
        msg = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": "919900112234",
            "message": "No conv test",
            "message_id": "wamid.webhook_no_conv",
            "content_type": "text",
            "whatsapp_account": "Test WA Webhook Account",
        })
        msg.flags.ignore_validate = True
        msg.db_insert()
        frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

        data = {
            "statuses": [{
                "id": "wamid.webhook_no_conv",
                "status": "sent",
            }]
        }
        update_message_status(data)

        msg.reload()
        self.assertEqual(msg.status, "sent")

    def test_update_template_status(self):
        """Test update_template_status updates template status via SQL."""
        # Create a template directly
        template_name = "test_webhook_tmpl-en"
        if not frappe.db.exists("WhatsApp Templates", template_name):
            doc = frappe.get_doc({
                "doctype": "WhatsApp Templates",
                "template_name": "test_webhook_tmpl",
                "actual_name": "test_webhook_tmpl",
                "template": "Webhook test template",
                "category": "TRANSACTIONAL",
                "language": frappe.db.get_value("Language", {"language_code": "en"}) or "en",
                "language_code": "en",
                "whatsapp_account": "Test WA Webhook Account",
                "status": "PENDING",
                "id": "webhook_tmpl_id_123",
            })
            doc.db_insert()
            frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

        data = {
            "event": "APPROVED",
            "message_template_id": "webhook_tmpl_id_123",
        }
        update_template_status(data)

        status = frappe.db.get_value("WhatsApp Templates", {"id": "webhook_tmpl_id_123"}, "status")
        self.assertEqual(status, "APPROVED")
