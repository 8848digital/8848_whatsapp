# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2022, Shridhar Patil and Contributors
# See license.txt

"""WhatsApp Notification setup: naming, validation and cache clearing."""

import frappe

from frappe_whatsapp.tests.notification_case import NotificationTestCase


class TestWhatsAppNotification(NotificationTestCase):
    """Tests for WhatsApp Notification doctype."""

    def test_notification_creation(self):
        """Test basic notification creation."""
        doc = self._make_notification()
        self.assertTrue(frappe.db.exists("WhatsApp Notification", doc.name))

    def test_notification_autoname(self):
        """Test notification is named from notification_name field."""
        doc = self._make_notification(notification_name="Test Notif Autoname")
        self.assertEqual(doc.name, "Test Notif Autoname")

    def test_validate_invalid_field_name(self):
        """Test validation fails for non-existent field name."""
        with self.assertRaises(frappe.ValidationError):
            self._make_notification(
                notification_name="Test Notif BadField",
                field_name="nonexistent_field_xyz"
            )

    def test_validate_valid_field_name(self):
        """Test validation passes for existing field name."""
        doc = self._make_notification(
            notification_name="Test Notif GoodField",
            field_name="email"
        )
        self.assertIsNotNone(doc.name)

    def test_validate_custom_attachment_requires_attach(self):
        """Test that custom_attachment requires either attach or attach_from_field."""
        with self.assertRaises(frappe.ValidationError):
            doc = frappe.get_doc({
                "doctype": "WhatsApp Notification",
                "notification_name": "Test Notif NoAttach",
                "notification_type": "DocType Event",
                "reference_doctype": "User",
                "field_name": "mobile_no",
                "doctype_event": "After Save",
                "template": "test_notif_template-en",
                "custom_attachment": 1,
                "attach": "",
                "attach_from_field": "",
            })
            doc.insert(ignore_permissions=True)

    def test_validate_set_property_after_alert_field_exists(self):
        """Test set_property_after_alert references existing field."""
        with self.assertRaises(frappe.ValidationError):
            doc = frappe.get_doc({
                "doctype": "WhatsApp Notification",
                "notification_name": "Test Notif BadProp",
                "notification_type": "DocType Event",
                "reference_doctype": "User",
                "field_name": "mobile_no",
                "doctype_event": "After Save",
                "template": "test_notif_template-en",
                "set_property_after_alert": "nonexistent_field_abc",
            })
            doc.insert(ignore_permissions=True)

    def test_field_name_optional_when_roles_set(self):
        """A roles-only notification can be saved."""
        doc = self._make_notification(
            notification_name="Test Notif RolesOnly",
            field_name="",
            roles=["System Manager"],
        )
        self.assertTrue(frappe.db.exists("WhatsApp Notification", doc.name))

    def test_neither_field_name_nor_roles_is_rejected(self):
        """Without a field or a role there is nobody to send to."""
        with self.assertRaises(frappe.ValidationError):
            self._make_notification(
                notification_name="Test Notif NoRecipient",
                field_name="",
            )

    def test_format_number(self):
        """Test format_number strips leading +."""
        doc = self._make_notification(notification_name="Test Notif Format")
        self.assertEqual(doc.format_number("+919900112233"), "919900112233")
        self.assertEqual(doc.format_number("919900112233"), "919900112233")

    def test_on_trash_clears_cache(self):
        """Test on_trash clears the notification map cache."""
        doc = self._make_notification(notification_name="Test Notif Cache")
        frappe.cache().set_value("whatsapp_notification_map", {"test": True})

        # Call on_trash directly to avoid side effects from doc.delete()
        # (delete triggers run_server_script_for_doc_event which rebuilds cache)
        doc.on_trash()

        cached = frappe.cache().get_value("whatsapp_notification_map")
        self.assertFalse(cached)


