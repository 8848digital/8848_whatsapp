# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""WhatsApp Templates kept in sync with Meta: create, delete and fetch."""

import json
from unittest.mock import patch

import frappe

from frappe_whatsapp.tests.template_case import TemplateTestCase


class TestWhatsAppTemplatesMeta(TemplateTestCase):
    """Calls to Meta's template API, with requests mocked."""

    @patch("frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_meta.make_post_request")
    def test_after_insert_creates_template_on_meta(self, mock_post):
        """Test after_insert sends template to Meta API."""
        mock_post.return_value = {
            "id": "new_template_id_123",
            "status": "PENDING",
        }

        doc = frappe.get_doc({
            "doctype": "WhatsApp Templates",
            "template_name": "test_tmpl_insert",
            "template": "Test body {{1}}",
            "sample_values": "World",
            "category": "TRANSACTIONAL",
            "language": frappe.db.get_value("Language", {"language_code": "en"}) or "en",
            "language_code": "en",
            "whatsapp_account": "Test WA Tmpl Account",
        })
        doc.insert(ignore_permissions=True)

        self.assertTrue(mock_post.called)
        call_args = mock_post.call_args
        sent_data = json.loads(call_args.kwargs.get("data", call_args[1].get("data", "")))
        self.assertEqual(sent_data["name"], "test_tmpl_insert")
        self.assertEqual(sent_data["language"], "en")
        self.assertEqual(sent_data["category"], "TRANSACTIONAL")
        self.assertTrue(any(c["type"] == "BODY" for c in sent_data["components"]))

    @patch("frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_meta.make_post_request")
    def test_after_insert_with_footer(self, mock_post):
        """Test template creation includes footer in components."""
        mock_post.return_value = {"id": "tmpl_footer_id", "status": "PENDING"}

        doc = frappe.get_doc({
            "doctype": "WhatsApp Templates",
            "template_name": "test_tmpl_footer",
            "template": "Body text",
            "footer": "Reply STOP to opt out",
            "category": "MARKETING",
            "language": frappe.db.get_value("Language", {"language_code": "en"}) or "en",
            "language_code": "en",
            "whatsapp_account": "Test WA Tmpl Account",
        })
        doc.insert(ignore_permissions=True)

        call_args = mock_post.call_args
        sent_data = json.loads(call_args.kwargs.get("data", call_args[1].get("data", "")))
        footer_components = [c for c in sent_data["components"] if c["type"] == "FOOTER"]
        self.assertEqual(len(footer_components), 1)
        self.assertEqual(footer_components[0]["text"], "Reply STOP to opt out")

    @patch("frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_meta.make_post_request")
    def test_after_insert_with_buttons(self, mock_post):
        """Test template creation includes buttons."""
        mock_post.return_value = {"id": "tmpl_btn_id", "status": "PENDING"}

        doc = frappe.get_doc({
            "doctype": "WhatsApp Templates",
            "template_name": "test_tmpl_buttons",
            "template": "Click below",
            "category": "TRANSACTIONAL",
            "language": frappe.db.get_value("Language", {"language_code": "en"}) or "en",
            "language_code": "en",
            "whatsapp_account": "Test WA Tmpl Account",
        })
        doc.append("buttons", {
            "button_type": "Quick Reply",
            "button_label": "Yes",
        })
        doc.append("buttons", {
            "button_type": "Visit Website",
            "button_label": "Visit",
            "website_url": "https://example.com",
            "url_type": "Static",
        })
        doc.insert(ignore_permissions=True)

        call_args = mock_post.call_args
        sent_data = json.loads(call_args.kwargs.get("data", call_args[1].get("data", "")))
        button_components = [c for c in sent_data["components"] if c["type"] == "BUTTONS"]
        self.assertEqual(len(button_components), 1)
        buttons = button_components[0]["buttons"]
        self.assertEqual(len(buttons), 2)
        self.assertEqual(buttons[0]["type"], "QUICK_REPLY")
        self.assertEqual(buttons[1]["type"], "URL")

    @patch("frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_meta.make_post_request")
    @patch("frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_meta.make_request")
    def test_on_trash_deletes_from_meta(self, mock_request, mock_post):
        """Test on_trash calls Meta API to delete template."""
        mock_post.return_value = {"id": "tmpl_trash_id", "status": "PENDING"}

        doc = frappe.get_doc({
            "doctype": "WhatsApp Templates",
            "template_name": "test_tmpl_trash",
            "template": "Delete me",
            "category": "TRANSACTIONAL",
            "language": frappe.db.get_value("Language", {"language_code": "en"}) or "en",
            "language_code": "en",
            "whatsapp_account": "Test WA Tmpl Account",
        })
        doc.insert(ignore_permissions=True)

        mock_request.return_value = {}
        doc.delete()

        # Verify DELETE was called on Meta API
        self.assertTrue(mock_request.called)
        delete_call = mock_request.call_args
        self.assertEqual(delete_call[0][0], "DELETE")
        self.assertIn("message_templates", delete_call[0][1])

    @patch("frappe.model.document.Document.get_password", return_value="mock_token")
    @patch("frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_fetch.make_request")
    @patch("frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_meta.make_post_request")
    def test_fetch_templates_from_meta(self, mock_post, mock_get, mock_get_password):
        """Test the fetch whitelisted function."""
        mock_get.return_value = {
            "data": [
                {
                    "name": "test_tmpl_fetched",
                    "status": "APPROVED",
                    "language": "en",
                    "category": "UTILITY",
                    "id": "fetched_tmpl_id",
                    "components": [
                        {"type": "BODY", "text": "Hello {{1}}, your order is ready"},
                        {"type": "FOOTER", "text": "Thank you"},
                    ]
                }
            ]
        }

        from frappe_whatsapp.frappe_whatsapp.api.v1.template import fetch
        result = fetch()
        self.assertEqual(result, "Successfully fetched templates from meta")

    def test_upsert_doc_without_hooks(self):
        """Test upsert_doc_without_hooks inserts and updates correctly."""
        from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_fetch import upsert_without_hooks as upsert_doc_without_hooks

        doc = self._make_template_without_hooks(template_name="test_tmpl_upsert")

        # Update template text
        doc.template = "Updated body text"
        upsert_doc_without_hooks(doc, "WhatsApp Button", "buttons")

        doc.reload()
        self.assertEqual(doc.template, "Updated body text")
