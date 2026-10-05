# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Outgoing WhatsApp Messages: the payload sent to Meta for each message type."""

import json
from unittest.mock import MagicMock, patch

import frappe

from frappe_whatsapp.tests.message_case import MessageTestCase


class TestWhatsAppMessageOutgoing(MessageTestCase):
    """Text, media, reply, reaction and template sends."""

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_outgoing_text_message(self, mock_post):
        """Test sending an outgoing text message."""
        mock_post.return_value = {
            "messages": [{"id": "wamid.test_outgoing_1"}],
            "contacts": [{"wa_id": "919900112255"}]
        }
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": "919900112255",
            "message": "Hello from test",
            "message_type": "Manual",
            "content_type": "text",
            "whatsapp_account": "Test WA Msg Account",
        })
        doc.insert(ignore_permissions=True)

        self.assertEqual(doc.message_id, "wamid.test_outgoing_1")
        self.assertEqual(doc.status, "Success")

        # Verify the API was called with correct data
        call_args = mock_post.call_args
        sent_data = json.loads(call_args.kwargs.get("data", call_args[1].get("data", "")))
        self.assertEqual(sent_data["messaging_product"], "whatsapp")
        self.assertEqual(sent_data["to"], "919900112255")
        self.assertEqual(sent_data["type"], "text")
        self.assertEqual(sent_data["text"]["body"], "Hello from test")

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_outgoing_text_message_with_plus_number(self, mock_post):
        """Test that + is stripped from phone numbers."""
        mock_post.return_value = {
            "messages": [{"id": "wamid.test_plus_1"}],
        }
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": "+919900112256",
            "message": "Test plus strip",
            "message_type": "Manual",
            "content_type": "text",
            "whatsapp_account": "Test WA Msg Account",
        })
        doc.insert(ignore_permissions=True)

        call_args = mock_post.call_args
        sent_data = json.loads(call_args.kwargs.get("data", call_args[1].get("data", "")))
        self.assertEqual(sent_data["to"], "919900112256")

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_outgoing_reply_message(self, mock_post):
        """Test sending a reply message includes context."""
        mock_post.return_value = {
            "messages": [{"id": "wamid.test_reply_1"}],
        }
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": "919900112257",
            "message": "Reply test",
            "message_type": "Manual",
            "content_type": "text",
            "is_reply": 1,
            "reply_to_message_id": "wamid.original_msg_123",
            "whatsapp_account": "Test WA Msg Account",
        })
        doc.insert(ignore_permissions=True)

        call_args = mock_post.call_args
        sent_data = json.loads(call_args.kwargs.get("data", call_args[1].get("data", "")))
        self.assertIn("context", sent_data)
        self.assertEqual(sent_data["context"]["message_id"], "wamid.original_msg_123")

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_outgoing_image_message(self, mock_post):
        """Test sending an image message."""
        mock_post.return_value = {
            "messages": [{"id": "wamid.test_image_1"}],
        }
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": "919900112258",
            "message": "Image caption",
            "message_type": "Manual",
            "content_type": "image",
            "attach": "https://example.com/image.jpg",
            "whatsapp_account": "Test WA Msg Account",
        })
        doc.insert(ignore_permissions=True)

        call_args = mock_post.call_args
        sent_data = json.loads(call_args.kwargs.get("data", call_args[1].get("data", "")))
        self.assertEqual(sent_data["type"], "image")
        self.assertEqual(sent_data["image"]["link"], "https://example.com/image.jpg")
        self.assertEqual(sent_data["image"]["caption"], "Image caption")

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_outgoing_reaction_message(self, mock_post):
        """Test sending a reaction message."""
        mock_post.return_value = {
            "messages": [{"id": "wamid.test_reaction_1"}],
        }
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": "919900112259",
            "message": "\U0001f44d",
            "message_type": "Manual",
            "content_type": "reaction",
            "reply_to_message_id": "wamid.react_to_msg",
            "whatsapp_account": "Test WA Msg Account",
        })
        doc.insert(ignore_permissions=True)

        call_args = mock_post.call_args
        sent_data = json.loads(call_args.kwargs.get("data", call_args[1].get("data", "")))
        self.assertEqual(sent_data["type"], "reaction")
        self.assertEqual(sent_data["reaction"]["emoji"], "\U0001f44d")
        self.assertEqual(sent_data["reaction"]["message_id"], "wamid.react_to_msg")

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_outgoing_message_api_failure(self, mock_post):
        """Test that outgoing message handles API failure."""
        mock_post.side_effect = Exception("API Error")
        frappe.flags.integration_request = MagicMock()
        frappe.flags.integration_request.json.return_value = {
            "error": {"message": "Invalid phone number", "error_user_title": "Error"}
        }

        with self.assertRaises(frappe.ValidationError):
            doc = frappe.get_doc({
                "doctype": "WhatsApp Message",
                "type": "Outgoing",
                "to": "919900112270",
                "message": "Fail test",
                "message_type": "Manual",
                "content_type": "text",
                "whatsapp_account": "Test WA Msg Account",
            })
            doc.insert(ignore_permissions=True)


