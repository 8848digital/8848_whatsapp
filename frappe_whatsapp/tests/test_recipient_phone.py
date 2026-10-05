# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Which number a user is messaged on, per WhatsApp Settings > Phone Number Source."""

from unittest.mock import patch

import frappe

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_recipients import (
    get_role_recipients,
)
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.recipient_phone import (
    SOURCE_EMPLOYEE_ONLY,
    SOURCE_EMPLOYEE_THEN_USER,
    SOURCE_USER_ONLY,
    SOURCE_USER_THEN_EMPLOYEE,
    resolve_phone,
)
from frappe_whatsapp.tests.helpers import IntegrationTestCase

ROLE = "_Test WA Role"


class TestResolvePhone(IntegrationTestCase):
    """Tests for the phone-source priority setting."""

    USER = "u@example.com"
    USER_NUMBERS = {USER: "9990001111"}
    EMPLOYEE_NUMBERS = {USER: "8880002222"}

    def test_user_only_ignores_employee(self):
        """"User Mobile No" uses the User number only."""
        self.assertEqual(
            resolve_phone(self.USER, SOURCE_USER_ONLY, self.USER_NUMBERS, self.EMPLOYEE_NUMBERS),
            "9990001111",
        )

    def test_employee_only_ignores_user(self):
        """"Employee Cell Number" uses the Employee number only."""
        self.assertEqual(
            resolve_phone(self.USER, SOURCE_EMPLOYEE_ONLY, self.USER_NUMBERS, self.EMPLOYEE_NUMBERS),
            "8880002222",
        )

    def test_user_then_employee_prefers_user(self):
        """User first: the User number wins when both exist."""
        self.assertEqual(
            resolve_phone(
                self.USER, SOURCE_USER_THEN_EMPLOYEE, self.USER_NUMBERS, self.EMPLOYEE_NUMBERS
            ),
            "9990001111",
        )

    def test_user_then_employee_falls_back(self):
        """User first: falls back to the Employee number."""
        self.assertEqual(
            resolve_phone(self.USER, SOURCE_USER_THEN_EMPLOYEE, {}, self.EMPLOYEE_NUMBERS),
            "8880002222",
        )

    def test_employee_then_user_falls_back(self):
        """Employee first: falls back to the User number."""
        self.assertEqual(
            resolve_phone(self.USER, SOURCE_EMPLOYEE_THEN_USER, self.USER_NUMBERS, {}),
            "9990001111",
        )

    def test_user_only_skips_employee_lookup(self):
        """Employee rows are not even queried when only User numbers are used."""
        notification = frappe._dict(
            name="_Test WA Notification",
            recipients=[frappe._dict(receiver_by_role=ROLE)],
        )
        settings = frappe._dict(role_phone_source=SOURCE_USER_ONLY, default_country_code="91")
        with patch(
            "frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_recipients.get_employee_numbers"
        ) as emp, patch(
            "frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_recipients.get_users_for_roles", return_value=["u@example.com"]
        ), patch(
            "frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_recipients.frappe.get_cached_doc", return_value=settings
        ):
            get_role_recipients(notification)

        emp.assert_not_called()
