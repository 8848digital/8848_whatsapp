# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Scheduler runs of WhatsApp Notifications, and disabled notifications staying quiet."""

from unittest.mock import patch

import frappe

from frappe_whatsapp.tests.notification_case import NotificationTestCase


class TestWhatsAppNotificationSchedule(NotificationTestCase):
    """Scheduler events and disabled notifications."""

    def test_disabled_notification_does_not_send(self):
        """Test that disabled notification does not trigger."""
        doc = self._make_notification(
            notification_name="Test Notif Disabled",
            disabled=1,
        )
        user = frappe.get_doc("User", "Administrator")
        user.mobile_no = "919900112299"

        # Should return early without sending
        result = doc.send_template_message(user)
        self.assertIsNone(result)

    def test_scheduler_tick_skips_role_based_doctype_event(self):
        """The "all" tick must not send DocType Event role notifications.

        trigger_whatsapp_notifications selects on event_frequency alone, and
        DocType Event notifications carry the hidden default "All", so this
        path is reached every few minutes in production.
        """
        doc = self._make_notification(
            notification_name="Test Notif TickSkipsDocEvent",
            field_name="",
            roles=["System Manager"],
        )
        doc.event_frequency = "All"

        target = (
            "frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification"
            ".notification_schedule.get_role_recipients"
        )
        with patch(target) as mock_roles, patch.object(doc, "send_simple_template") as mock_send:
            doc.send_scheduled_message()

        self.assertFalse(mock_roles.called)
        self.assertFalse(mock_send.called)

    def test_scheduler_tick_sends_role_based_scheduler_event(self):
        """Genuine Scheduler Event role notifications still send."""
        doc = self._make_notification(
            notification_name="Test Notif TickSendsScheduler",
            notification_type="Scheduler Event",
            field_name="",
            roles=["System Manager"],
        )

        target = (
            "frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification"
            ".notification_schedule.get_role_recipients"
        )
        with patch(
            target,
            return_value=(
                [{"user": "a@example.com", "full_name": "A", "phone": "919900110001"}],
                [],
            ),
        ), patch.object(doc, "send_simple_template") as mock_send:
            doc.send_scheduled_message()

        self.assertTrue(mock_send.called)
        self.assertEqual(doc._contact_list, ["919900110001"])

    def test_scheduler_event_notification(self):
        """Test creating a scheduler event notification."""
        doc = frappe.get_doc({
            "doctype": "WhatsApp Notification",
            "notification_name": "Test Notif Scheduler",
            "notification_type": "Scheduler Event",
            "reference_doctype": "User",
            "event_frequency": "Daily",
            "template": "test_notif_template-en",
            "condition": "",
        })
        doc.insert(ignore_permissions=True)
        self.assertEqual(doc.notification_type, "Scheduler Event")
        self.assertEqual(doc.event_frequency, "Daily")
