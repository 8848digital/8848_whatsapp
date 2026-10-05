# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2022, Shridhar Patil and Contributors
# See license.txt

"""WhatsApp Templates basics: naming, defaults, sample files and headers."""

from unittest.mock import MagicMock, patch

import frappe

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_meta import build_header
from frappe_whatsapp.tests.template_case import TemplateTestCase


class TestWhatsAppTemplates(TemplateTestCase):
    """Tests for WhatsApp Templates doctype."""

    def test_template_autoname(self):
        """Test template autoname format: template_name-language_code."""
        doc = self._make_template_without_hooks(template_name="test_tmpl_autoname")
        self.assertEqual(doc.name, "test_tmpl_autoname-en")

    @patch("frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_meta.make_post_request")
    def test_language_code_set_on_validate(self, mock_post):
        """Test language_code is derived from language field on validate."""
        mock_post.return_value = {}
        doc = self._make_template_without_hooks(template_name="test_tmpl_langcode")
        doc.language_code = ""
        doc.language = frappe.db.get_value("Language", {"language_code": "en"}) or "en"
        doc.validate()
        self.assertTrue(len(doc.language_code) > 0)

    def test_set_whatsapp_account_default(self):
        """Test whatsapp_account is set to default if missing."""
        doc = self._make_template_without_hooks(
            template_name="test_tmpl_default_acct",
            whatsapp_account=""
        )
        doc.whatsapp_account = ""
        doc.set_whatsapp_account()
        self.assertTrue(len(doc.whatsapp_account) > 0)

    def test_read_local_file_uses_file_doctype(self):
        """read_sample_file resolves site files through the File doctype, not raw paths."""
        from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.template_media import read_sample_file

        mock_file = MagicMock()
        mock_file.get_content.return_value = b"binary-content"
        with patch("frappe.get_doc", return_value=mock_file) as mock_get_doc:
            content, _mime_type = read_sample_file("/files/test_image.png")

        self.assertEqual(content, b"binary-content")
        mock_get_doc.assert_called_once_with("File", {"file_url": "/files/test_image.png"})

    def test_get_header_text(self):
        """Test get_header for TEXT header type."""
        doc = self._make_template_without_hooks(
            template_name="test_tmpl_hdr_text",
            header_type="TEXT",
            header="Order Update"
        )
        header = build_header(doc)
        self.assertEqual(header["type"], "header")
        self.assertEqual(header["format"], "TEXT")
        self.assertEqual(header["text"], "Order Update")

    def test_get_header_text_with_sample(self):
        """Test get_header for TEXT header with sample values."""
        doc = self._make_template_without_hooks(
            template_name="test_tmpl_hdr_sample",
            header_type="TEXT",
            header="Hello {{1}}",
            sample_values="John"
        )
        doc.sample = "John"
        header = build_header(doc)
        self.assertEqual(header["format"], "TEXT")
        self.assertIn("example", header)
        self.assertEqual(header["example"]["header_text"], ["John"])

    def test_graph_url_uses_template_account(self):
        """Meta calls use the template's WhatsApp Account url, version and business id."""
        from frappe_whatsapp.utils.meta_api import get_graph_url

        doc = self._make_template_without_hooks(template_name="test_tmpl_settings")
        account = frappe.get_doc("WhatsApp Account", doc.whatsapp_account)
        url = get_graph_url(account, f"{account.business_id}/message_templates")
        self.assertEqual(url, "https://graph.facebook.com/v17.0/tmpl_test_business_id/message_templates")


