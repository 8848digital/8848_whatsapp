# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, Shridhar Patil and Contributors
# See license.txt

"""The webhook endpoint: Meta's subscription check and incoming messages."""

from unittest.mock import patch

import frappe

from frappe_whatsapp.tests.webhook_case import WebhookEndpointTestCase


class TestWebhookEndpoint(WebhookEndpointTestCase):
    """Tests for the webhook endpoint."""

    def test_webhook_get_verification(self):
        """Test GET webhook verification."""
        mock_request = self._make_mock_request("GET")
        frappe.local.form_dict = frappe._dict({
            "hub.challenge": "test_challenge_123",
            "hub.verify_token": "Test WA Webhook EP Account",
            "hub.mode": "subscribe",
        })

        with patch("frappe_whatsapp.frappe_whatsapp.api.v1.webhook.frappe.request", mock_request):
            from frappe_whatsapp.frappe_whatsapp.api.v1.webhook import webhook
            response = webhook()
            self.assertEqual(response.status_code, 200)

    def test_webhook_get_wrong_token(self):
        """Test GET webhook with wrong verify token."""
        mock_request = self._make_mock_request("GET")
        frappe.local.form_dict = frappe._dict({
            "hub.challenge": "test_challenge",
            "hub.verify_token": "wrong_token",
        })

        with patch("frappe_whatsapp.frappe_whatsapp.api.v1.webhook.frappe.request", mock_request):
            from frappe_whatsapp.frappe_whatsapp.api.v1.webhook import webhook
            with self.assertRaises(frappe.ValidationError):
                webhook()

    def test_webhook_post_text_message(self):
        """Test POST webhook with incoming text message."""
        mock_request = self._make_mock_request("POST")
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "metadata": {"phone_number_id": "webhook_ep_phone_id"},
                        "contacts": [{"profile": {"name": "Test Sender"}}],
                        "messages": [{
                            "from": "919900112288",
                            "id": "wamid.webhook_ep_text_1",
                            "type": "text",
                            "text": {"body": "Hello from webhook test"},
                        }]
                    }
                }]
            }]
        }
        frappe.local.form_dict = frappe._dict(payload)

        with patch("frappe_whatsapp.frappe_whatsapp.api.v1.webhook.frappe.request", mock_request):
            from frappe_whatsapp.frappe_whatsapp.api.v1.webhook import webhook
            webhook()

        self.assertTrue(
            frappe.db.exists("WhatsApp Message", {"message_id": "wamid.webhook_ep_text_1"})
        )
        msg = frappe.get_doc("WhatsApp Message", {"message_id": "wamid.webhook_ep_text_1"})
        self.assertEqual(msg.type, "Incoming")
        self.assertEqual(msg.message, "Hello from webhook test")
        self.assertEqual(msg.content_type, "text")

    def test_webhook_post_reaction_message(self):
        """Test POST webhook with reaction message."""
        mock_request = self._make_mock_request("POST")
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "metadata": {"phone_number_id": "webhook_ep_phone_id"},
                        "contacts": [{"profile": {"name": "Reactor"}}],
                        "messages": [{
                            "from": "919900112289",
                            "id": "wamid.webhook_ep_reaction_1",
                            "type": "reaction",
                            "reaction": {
                                "emoji": "\U0001f44d",
                                "message_id": "wamid.original_reacted_to"
                            },
                        }]
                    }
                }]
            }]
        }
        frappe.local.form_dict = frappe._dict(payload)

        with patch("frappe_whatsapp.frappe_whatsapp.api.v1.webhook.frappe.request", mock_request):
            from frappe_whatsapp.frappe_whatsapp.api.v1.webhook import webhook
            webhook()

        self.assertTrue(
            frappe.db.exists("WhatsApp Message", {"message_id": "wamid.webhook_ep_reaction_1"})
        )
        msg = frappe.get_doc("WhatsApp Message", {"message_id": "wamid.webhook_ep_reaction_1"})
        self.assertEqual(msg.content_type, "reaction")
        self.assertEqual(msg.message, "\U0001f44d")

    def test_webhook_post_button_message(self):
        """Test POST webhook with button reply message."""
        mock_request = self._make_mock_request("POST")
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "metadata": {"phone_number_id": "webhook_ep_phone_id"},
                        "contacts": [{"profile": {"name": "Button User"}}],
                        "messages": [{
                            "from": "919900112290",
                            "id": "wamid.webhook_ep_button_1",
                            "type": "button",
                            "button": {"text": "Yes, confirm"},
                        }]
                    }
                }]
            }]
        }
        frappe.local.form_dict = frappe._dict(payload)

        with patch("frappe_whatsapp.frappe_whatsapp.api.v1.webhook.frappe.request", mock_request):
            from frappe_whatsapp.frappe_whatsapp.api.v1.webhook import webhook
            webhook()

        msg = frappe.get_doc("WhatsApp Message", {"message_id": "wamid.webhook_ep_button_1"})
        self.assertEqual(msg.content_type, "button")
        self.assertEqual(msg.message, "Yes, confirm")

    def test_webhook_post_reply_message(self):
        """Test POST webhook with reply context."""
        mock_request = self._make_mock_request("POST")
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "metadata": {"phone_number_id": "webhook_ep_phone_id"},
                        "contacts": [{"profile": {"name": "Reply User"}}],
                        "messages": [{
                            "from": "919900112291",
                            "id": "wamid.webhook_ep_reply_1",
                            "type": "text",
                            "text": {"body": "This is a reply"},
                            "context": {"id": "wamid.original_msg_replied_to"},
                        }]
                    }
                }]
            }]
        }
        frappe.local.form_dict = frappe._dict(payload)

        with patch("frappe_whatsapp.frappe_whatsapp.api.v1.webhook.frappe.request", mock_request):
            from frappe_whatsapp.frappe_whatsapp.api.v1.webhook import webhook
            webhook()

        msg = frappe.get_doc("WhatsApp Message", {"message_id": "wamid.webhook_ep_reply_1"})
        self.assertEqual(msg.is_reply, 1)
        self.assertEqual(msg.reply_to_message_id, "wamid.original_msg_replied_to")


