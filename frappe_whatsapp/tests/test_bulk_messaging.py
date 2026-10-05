# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, Shridhar Patil and Contributors
# See license.txt

import json
from unittest.mock import patch

import frappe
from frappe_whatsapp.tests.helpers import IntegrationTestCase, make_test_account, make_test_template, use_test_account

from frappe_whatsapp.frappe_whatsapp.api.v1.bulk_messaging import (
    get_progress,
    import_recipients,
    retry_failed,
)
from frappe_whatsapp.frappe_whatsapp.tasks import update_bulk_message_statuses as schedule_bulk_messages


class TestBulkMessagingUtils(IntegrationTestCase):
    """Tests for bulk messaging utility functions."""

    @classmethod
    def setUpClass(cls):
        """Create the shared test records once for the class."""
        super().setUpClass()
        make_test_account("Test WA BulkUtil Account", "bulkutil_test")
        make_test_template("test_bulkutil_template", "Test WA BulkUtil Account", "Hello {{1}}", "User")
        cls._ensure_test_user_with_mobile()

    @classmethod
    def _ensure_test_user_with_mobile(cls):
        """Ensure there's at least one user with mobile_no set for import tests."""
        if not frappe.db.get_value("User", "Administrator", "mobile_no"):
            frappe.db.set_value("User", "Administrator", "mobile_no", "919900000001")
            frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

    def setUp(self):
        """Make the bulk-utils test account the default for this test."""
        use_test_account("Test WA BulkUtil Account", "test_bulkutil_token")

    def tearDown(self):
        """Delete the bulk messages and recipient lists this test created."""
        for name in frappe.get_all("Bulk WhatsApp Message", filters={"title": ["like", "Test BulkUtil%"]}, pluck="name"):
            frappe.db.set_value("Bulk WhatsApp Message", name, "docstatus", 2)
            frappe.delete_doc("Bulk WhatsApp Message", name, force=True)
        for name in frappe.get_all("WhatsApp Recipient List", filters={"list_name": ["like", "Test BulkUtil%"]}, pluck="name"):
            frappe.delete_doc("WhatsApp Recipient List", name, force=True)
        frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

    def _make_bulk_message(self, title="Test BulkUtil Msg"):
        """Create a bulk message for testing."""
        doc = frappe.get_doc({
            "doctype": "Bulk WhatsApp Message",
            "title": title,
            "recipient_type": "Individual",
            "use_template": 1,
            "template": "test_bulkutil_template-en",
            "variable_type": "Common",
            "whatsapp_account": "Test WA BulkUtil Account",
        })
        doc.append("recipients", {"mobile_number": "919900112233", "recipient_name": "User 1"})
        doc.append("recipients", {"mobile_number": "919900112244", "recipient_name": "User 2"})
        doc.insert(ignore_permissions=True)
        return doc

    def test_get_progress(self):
        """Test get_progress whitelisted function."""
        doc = self._make_bulk_message(title="Test BulkUtil Progress")
        progress = get_progress(doc.name)
        self.assertIn("total", progress)
        self.assertEqual(progress["total"], 2)

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_retry_failed_util(self, mock_post):
        """Test retry_failed whitelisted function."""
        mock_post.return_value = {"messages": [{"id": "wamid.retry_util_1"}]}
        doc = self._make_bulk_message(title="Test BulkUtil Retry")

        # Create a failed message
        failed_msg = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": "919900112255",
            "message": "Failed util msg",
            "message_type": "Manual",
            "content_type": "text",
            "status": "Failed",
            "bulk_message_reference": doc.name,
            "whatsapp_account": "Test WA BulkUtil Account",
            "message_id": "wamid.failed_util_1",
        })
        failed_msg.flags.ignore_validate = True
        failed_msg.db_insert()
        frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture must be visible to later queries

        result = retry_failed(doc.name)
        self.assertTrue(result)

    def test_import_recipients(self):
        """Test import_recipients whitelisted function."""
        rec_list = frappe.get_doc({
            "doctype": "WhatsApp Recipient List",
            "list_name": "Test BulkUtil Import List",
        })
        rec_list.append("recipients", {"mobile_number": "placeholder"})
        rec_list.insert(ignore_permissions=True)

        count = import_recipients(
            list_name=rec_list.name,
            doctype="User",
            mobile_field="mobile_no",
            name_field="full_name",
            filters=json.dumps({"mobile_no": ["is", "set"]}),
            limit=5,
        )
        self.assertGreater(count, 0)

    def test_import_recipients_with_string_filters(self):
        """Test import_recipients handles string filters."""
        rec_list = frappe.get_doc({
            "doctype": "WhatsApp Recipient List",
            "list_name": "Test BulkUtil Import Str",
        })
        rec_list.append("recipients", {"mobile_number": "placeholder"})
        rec_list.insert(ignore_permissions=True)

        # Pass filters as string (as it would come from a whitelisted call)
        count = import_recipients(
            list_name=rec_list.name,
            doctype="User",
            mobile_field="mobile_no",
            filters='{"mobile_no": ["is", "set"]}',
            limit=5,
        )
        self.assertGreater(count, 0)

    def test_schedule_bulk_messages(self):
        """Test schedule_bulk_messages background job."""
        # This just ensures the function runs without error
        # when there are no queued bulk messages
        schedule_bulk_messages()
