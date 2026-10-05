# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2022, Shridhar Patil and Contributors
# See license.txt

import json
from unittest.mock import patch

import frappe
from frappe_whatsapp.tests.message_case import MessageTestCase


class TestWhatsAppMessage(MessageTestCase):
    """Tests for WhatsApp Message doctype."""

    def test_incoming_message_creation(self):
        """Test creating an incoming WhatsApp message."""
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Incoming",
            "from": "919900112233",
            "message": "Hello World",
            "message_id": "wamid.test_incoming_1",
            "content_type": "text",
            "whatsapp_account": "Test WA Msg Account",
        })
        doc.insert(ignore_permissions=True)
        self.assertTrue(frappe.db.exists("WhatsApp Message", doc.name))
        self.assertEqual(doc.type, "Incoming")

    def test_set_whatsapp_account_default(self):
        """Test that whatsapp_account is auto-set to default when not provided."""
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Incoming",
            "from": "919900112244",
            "message": "Test default account",
            "message_id": "wamid.test_default_1",
            "content_type": "text",
        })
        doc.insert(ignore_permissions=True)
        self.assertEqual(doc.whatsapp_account, "Test WA Msg Account")

    def test_create_whatsapp_profile_on_insert(self):
        """Test that a WhatsApp Profile is created when a message is inserted."""
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Incoming",
            "from": "919900112260",
            "message": "Profile creation test",
            "message_id": "wamid.test_profile_create",
            "content_type": "text",
            "profile_name": "Test Profile User",
            "whatsapp_account": "Test WA Msg Account",
        })
        doc.insert(ignore_permissions=True)

        self.assertTrue(
            frappe.db.exists("WhatsApp Profiles", {"number": "919900112260"})
        )

    def test_update_profile_name_on_update(self):
        """Test that profile name is updated when message profile_name changes."""
        # First create a profile
        profile = frappe.get_doc({
            "doctype": "WhatsApp Profiles",
            "profile_name": "Original Name",
            "number": "919900112261",
        })
        profile.insert(ignore_permissions=True)

        # Create incoming message with new profile name
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Incoming",
            "from": "919900112261",
            "message": "Update profile test",
            "message_id": "wamid.test_profile_update",
            "content_type": "text",
            "profile_name": "Updated Name",
            "whatsapp_account": "Test WA Msg Account",
        })
        doc.insert(ignore_permissions=True)

        profile.reload()
        self.assertEqual(profile.profile_name, "Updated Name")

    def test_format_number_method(self):
        """Test the format_number instance method."""
        doc = frappe.new_doc("WhatsApp Message")
        self.assertEqual(doc.format_number("+919900112233"), "919900112233")
        self.assertEqual(doc.format_number("919900112233"), "919900112233")

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_send_read_receipt(self, mock_post):
        """Test sending a read receipt."""
        mock_post.return_value = {"success": True}

        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Incoming",
            "from": "919900112262",
            "message": "Read receipt test",
            "message_id": "wamid.test_read_receipt",
            "content_type": "text",
            "whatsapp_account": "Test WA Msg Account",
        })
        doc.insert(ignore_permissions=True)

        result = doc.send_read_receipt()
        self.assertTrue(result)

        call_args = mock_post.call_args
        sent_data = json.loads(call_args.kwargs.get("data", call_args[1].get("data", "")))
        self.assertEqual(sent_data["status"], "read")
        self.assertEqual(sent_data["message_id"], "wamid.test_read_receipt")


