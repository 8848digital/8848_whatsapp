# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Webhook POSTs that are not messages: delivery statuses, template statuses and the log."""

from unittest.mock import patch

import frappe

from frappe_whatsapp.tests.webhook_case import WebhookEndpointTestCase


class TestWebhookEvents(WebhookEndpointTestCase):
    """Status updates and logging through the webhook endpoint."""

    def test_webhook_post_status_update(self):
        """Test POST webhook with status update (no messages)."""
        # Create a message to update
        msg = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": "919900112292",
            "message": "Status update test",
            "message_id": "wamid.webhook_ep_status_1",
            "content_type": "text",
            "whatsapp_account": "Test WA Webhook EP Account",
        })
        msg.flags.ignore_validate = True
        msg.db_insert()
        frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

        mock_request = self._make_mock_request("POST")
        payload = {
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "metadata": {"phone_number_id": "webhook_ep_phone_id"},
                        "statuses": [{
                            "id": "wamid.webhook_ep_status_1",
                            "status": "read",
                            "conversation": {"id": "conv_456"}
                        }]
                    }
                }]
            }]
        }
        frappe.local.form_dict = frappe._dict(payload)

        with patch("frappe_whatsapp.frappe_whatsapp.api.v1.webhook.frappe.request", mock_request):
            from frappe_whatsapp.frappe_whatsapp.api.v1.webhook import webhook
            webhook()

        msg.reload()
        self.assertEqual(msg.status, "read")
        self.assertEqual(msg.conversation_id, "conv_456")

    def test_webhook_post_template_status_update(self):
        """Template status updates have no metadata.phone_number_id; the handler
        must still route them to update_status. Regression for PR #231."""
        template_id = "webhook_ep_tmpl_id_status"
        template_name = "ep_status_template-en"

        # Seed the template (or reset its status if a prior run left it APPROVED)
        if frappe.db.exists("WhatsApp Templates", template_name):
            frappe.db.set_value(
                "WhatsApp Templates", template_name, "status", "PENDING"
            )
        else:
            doc = frappe.get_doc({
                "doctype": "WhatsApp Templates",
                "template_name": "ep_status_template",
                "actual_name": "ep_status_template",
                "template": "Status webhook regression template",
                "category": "TRANSACTIONAL",
                "language": frappe.db.get_value("Language", {"language_code": "en"}) or "en",
                "language_code": "en",
                "whatsapp_account": "Test WA Webhook EP Account",
                "status": "PENDING",
                "id": template_id,
            })
            doc.db_insert()
        frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

        mock_request = self._make_mock_request("POST")
        payload = {
            "entry": [{
                "changes": [{
                    "field": "message_template_status_update",
                    "value": {
                        "event": "APPROVED",
                        "message_template_id": template_id,
                        "message_template_name": "ep_status_template",
                        "message_template_language": "en_US",
                        "reason": None,
                    },
                }],
            }],
        }
        frappe.local.form_dict = frappe._dict(payload)

        with patch("frappe_whatsapp.frappe_whatsapp.api.v1.webhook.frappe.request", mock_request):
            from frappe_whatsapp.frappe_whatsapp.api.v1.webhook import webhook
            webhook()

        status = frappe.db.get_value(
            "WhatsApp Templates", {"id": template_id}, "status"
        )
        self.assertEqual(status, "APPROVED")

    def test_webhook_creates_notification_log(self):
        """Test that webhook POST creates a notification log entry."""
        mock_request = self._make_mock_request("POST")
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "metadata": {"phone_number_id": "webhook_ep_phone_id"},
                        "contacts": [{"profile": {"name": "Log Test"}}],
                        "messages": [{
                            "from": "919900112293",
                            "id": "wamid.webhook_ep_log_1",
                            "type": "text",
                            "text": {"body": "Log test"},
                        }]
                    }
                }]
            }]
        }
        frappe.local.form_dict = frappe._dict(payload)

        with patch("frappe_whatsapp.frappe_whatsapp.api.v1.webhook.frappe.request", mock_request):
            from frappe_whatsapp.frappe_whatsapp.api.v1.webhook import webhook
            webhook()

        # Should have created a notification log
        logs = frappe.get_all("WhatsApp Notification Log", filters={"template": "Webhook"})
        self.assertTrue(len(logs) > 0)
