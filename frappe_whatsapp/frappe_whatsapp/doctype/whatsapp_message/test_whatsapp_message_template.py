# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Template messages sent through the send_template endpoint."""

import json
from unittest.mock import patch

import frappe

from frappe_whatsapp.tests.message_case import MessageTestCase


class TestWhatsAppMessageTemplate(MessageTestCase):
    """send_template endpoint and the template payload."""

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_send_template_whitelisted(self, mock_post):
        """Test the send_template whitelisted function."""
        mock_post.return_value = {
            "messages": [{"id": "wamid.test_template_wl"}],
        }

        # First create a template (without hooks to avoid Meta API calls)
        if not frappe.db.exists("WhatsApp Templates", "test_msg_template-en"):
            frappe.get_doc({
                "doctype": "WhatsApp Templates",
                "template_name": "test_msg_template",
                "actual_name": "test_msg_template",
                "template": "Hello {{1}}",
                "category": "TRANSACTIONAL",
                "language": frappe.db.get_value("Language", {"language_code": "en"}) or "en",
                "language_code": "en",
                "whatsapp_account": "Test WA Msg Account",
                "status": "APPROVED",
                "id": "test_template_id_123",
            }).db_insert()
            frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

        from frappe_whatsapp.frappe_whatsapp.api.v1.message import send_template
        send_template(
            to="919900112263",
            reference_doctype="User",
            reference_name="Administrator",
            template="test_msg_template-en"
        )

        self.assertTrue(
            frappe.db.exists("WhatsApp Message", {"to": "919900112263", "message_type": "Template"})
        )

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_send_template_omits_static_buttons(self, mock_post):
        """Static Call Phone / Visit Website buttons must NOT appear in the
        outgoing components payload — Meta rejects sub_type=phone_number and
        applies static buttons from the approved template automatically.
        See issue #188.
        """
        mock_post.return_value = {"messages": [{"id": "wamid.test_buttons"}]}

        template_name = "test_msg_buttons_template-en"
        if not frappe.db.exists("WhatsApp Templates", template_name):
            tmpl = frappe.get_doc({
                "doctype": "WhatsApp Templates",
                "template_name": "test_msg_buttons_template",
                "actual_name": "test_msg_buttons_template",
                "template": "Hello",
                "category": "TRANSACTIONAL",
                "language": frappe.db.get_value("Language", {"language_code": "en"}) or "en",
                "language_code": "en",
                "whatsapp_account": "Test WA Msg Account",
                "status": "APPROVED",
                "id": "test_template_buttons_id",
                "name": template_name,
            })
            tmpl.flags.ignore_validate = True
            tmpl.db_insert()
            # Link child rows manually — append() before the parent has a
            # name leaves parent blank, so we wire them up here.
            buttons = [
                {"button_type": "Quick Reply", "button_label": "Yes"},
                {
                    "button_type": "Call Phone",
                    "button_label": "Call Us",
                    "phone_number": "+919876543210",
                },
                {
                    "button_type": "Visit Website",
                    "button_label": "Homepage",
                    "website_url": "https://example.com",
                    "url_type": "Static",
                },
            ]
            for idx, data in enumerate(buttons, start=1):
                row = frappe.get_doc({
                    "doctype": "WhatsApp Button",
                    "parent": template_name,
                    "parenttype": "WhatsApp Templates",
                    "parentfield": "buttons",
                    "idx": idx,
                    **data,
                })
                row.db_insert()
            frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": "919900112264",
            "message_type": "Template",
            "content_type": "text",
            "template": template_name,
            "whatsapp_account": "Test WA Msg Account",
        })
        doc.insert(ignore_permissions=True)

        sent_data = json.loads(mock_post.call_args.kwargs["data"])
        components = sent_data["template"]["components"]
        sub_types = [c.get("sub_type") for c in components if c.get("type") == "button"]
        self.assertNotIn("phone_number", sub_types)
        self.assertNotIn("url", sub_types)  # static URL button also excluded
        self.assertIn("quick_reply", sub_types)
