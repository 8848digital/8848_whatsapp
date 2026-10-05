# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Who a WhatsApp Notification goes to, and when it is sent."""

import json
from unittest.mock import MagicMock, patch

import frappe

from frappe_whatsapp.tests.notification_case import NotificationTestCase


class TestWhatsAppNotificationSending(NotificationTestCase):
    """Recipients, sending and scheduler runs."""

    def test_get_recipients_uses_field_name(self):
        """Existing single-field behaviour is unchanged."""
        doc = self._make_notification(notification_name="Test Notif RecipField")
        user = frappe.get_doc("User", "Administrator")
        user.mobile_no = "919900112233"

        self.assertEqual(
            doc.get_recipients(user, user.as_dict()), (["919900112233"], [])
        )

    def test_get_recipients_explicit_phone_wins(self):
        """An explicit phone_no is the only recipient."""
        doc = self._make_notification(
            notification_name="Test Notif RecipExplicit",
            roles=["System Manager"],
        )
        user = frappe.get_doc("User", "Administrator")
        user.mobile_no = "919900112233"

        self.assertEqual(
            doc.get_recipients(user, user.as_dict(), phone_no="919900110000"),
            (["919900110000"], []),
        )

    def test_get_recipients_separates_field_from_roles(self):
        """Field number sends inline; role numbers are returned separately."""
        doc = self._make_notification(
            notification_name="Test Notif RecipMerge",
            roles=["System Manager"],
        )
        user = frappe.get_doc("User", "Administrator")
        user.mobile_no = "919900112233"

        with patch(
            "frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification"
            ".notification_sender.get_role_recipients",
            return_value=(
                [
                    {"user": "a@example.com", "full_name": "A", "phone": "919900112244"},
                    # Same number as the field, must not be messaged twice.
                    {"user": "b@example.com", "full_name": "B", "phone": "919900112233"},
                ],
                [],
            ),
        ):
            inline, role = doc.get_recipients(user, user.as_dict())

        self.assertEqual(inline, ["919900112233"])
        self.assertEqual(role, ["919900112244"])

    @patch("frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_sender.frappe.enqueue")
    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_role_recipients_are_queued_not_sent_inline(self, mock_post, mock_enqueue):
        """Role sends are handed to a background job."""
        doc = self._make_notification(
            notification_name="Test Notif Multi",
            field_name="",
            roles=["System Manager"],
        )
        user = frappe.get_doc("User", "Administrator")

        with patch(
            "frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification"
            ".notification_sender.get_role_recipients",
            return_value=(
                [
                    {"user": "a@example.com", "full_name": "A", "phone": "919900110001"},
                    {"user": "b@example.com", "full_name": "B", "phone": "919900110002"},
                ],
                [],
            ),
        ):
            doc.send_template_message(user)

        # Nothing sent in the request itself.
        self.assertFalse(mock_post.called)

        self.assertTrue(mock_enqueue.called)
        kwargs = mock_enqueue.call_args.kwargs
        self.assertEqual(kwargs["numbers"], ["919900110001", "919900110002"])
        self.assertEqual(kwargs["notification"], doc.name)
        self.assertIsNone(kwargs["data"]["to"])

    @patch("frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_sender.frappe.enqueue")
    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_field_recipient_still_sends_inline(self, mock_post, mock_enqueue):
        """A field-based notification is unaffected by the queue change."""
        mock_post.return_value = {"messages": [{"id": "wamid.inline_1"}]}
        frappe.flags.integration_request = MagicMock()
        frappe.flags.integration_request.json.return_value = {
            "messages": [{"id": "wamid.inline_1"}]
        }

        doc = self._make_notification(notification_name="Test Notif InlineOnly")
        user = frappe.get_doc("User", "Administrator")
        user.mobile_no = "919900112233"

        doc.send_template_message(user)

        self.assertEqual(mock_post.call_count, 1)
        self.assertFalse(mock_enqueue.called)
        sent = json.loads(
            mock_post.call_args.kwargs.get("data", mock_post.call_args[1].get("data", ""))
        )
        self.assertEqual(sent["to"], "919900112233")

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_no_resolvable_recipients_does_not_send(self, mock_post):
        """No numbers means no request, not an error."""
        doc = self._make_notification(
            notification_name="Test Notif NoNumbers",
            field_name="",
            roles=["System Manager"],
        )
        user = frappe.get_doc("User", "Administrator")

        with patch(
            "frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification"
            ".notification_sender.get_role_recipients",
            return_value=([], [{"user": "a@example.com", "reason": "no phone number"}]),
        ):
            doc.send_template_message(user)

        self.assertFalse(mock_post.called)

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_send_template_message(self, mock_post):
        """Test send_template_message sends correct data."""
        mock_post.return_value = {
            "messages": [{"id": "wamid.notif_test_1"}],
            "contacts": [{"wa_id": "919900112233"}]
        }
        # Set integration_request flag (used in finally block of notify())
        frappe.flags.integration_request = MagicMock()
        frappe.flags.integration_request.json.return_value = {
            "messages": [{"id": "wamid.notif_test_1"}]
        }

        doc = self._make_notification(
            notification_name="Test Notif Send",
            field_name="mobile_no",
            fields=["first_name", "name"],
        )

        # Create a mock source document
        user = frappe.get_doc("User", "Administrator")
        user.mobile_no = "919900112233"

        doc.send_template_message(user)

        self.assertTrue(mock_post.called)
        call_args = mock_post.call_args
        sent_data = json.loads(call_args.kwargs.get("data", call_args[1].get("data", "")))
        self.assertEqual(sent_data["messaging_product"], "whatsapp")
        self.assertEqual(sent_data["to"], "919900112233")
        self.assertEqual(sent_data["type"], "template")
        self.assertEqual(sent_data["template"]["name"], "test_notif_template")

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_send_template_message_with_condition(self, mock_post):
        """Test that condition evaluation works."""
        mock_post.return_value = {
            "messages": [{"id": "wamid.notif_cond_1"}],
        }
        # Set integration_request flag (used in finally block of notify())
        frappe.flags.integration_request = MagicMock()
        frappe.flags.integration_request.json.return_value = {
            "messages": [{"id": "wamid.notif_cond_1"}]
        }

        doc = self._make_notification(
            notification_name="Test Notif Condition",
            field_name="mobile_no",
            condition="doc.enabled == 1",
        )

        # User with enabled=1 should trigger
        user = frappe.get_doc("User", "Administrator")
        user.mobile_no = "919900112299"
        user.enabled = 1
        doc.send_template_message(user)
        self.assertTrue(mock_post.called)

    @patch("frappe_whatsapp.utils.meta_api.make_post_request")
    def test_send_template_message_condition_not_met(self, mock_post):
        """Test that message is not sent when condition is not met."""
        doc = self._make_notification(
            notification_name="Test Notif NoSend",
            field_name="mobile_no",
            condition="doc.enabled == 0",
        )

        user = frappe.get_doc("User", "Administrator")
        user.mobile_no = "919900112299"
        user.enabled = 1
        doc.send_template_message(user)

        self.assertFalse(mock_post.called)


