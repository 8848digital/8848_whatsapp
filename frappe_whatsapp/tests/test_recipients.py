# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and Contributors
# See license.txt

import frappe

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.notification_recipients import (
    get_role_recipients,
    get_users_for_roles,
)
from frappe_whatsapp.tests.helpers import IntegrationTestCase

ROLE = "_Test WA Role"
OTHER_ROLE = "_Test WA Role Two"


def make_role_users(with_disabled_user=False):
    """
    Create the two test roles and users holding them, with and without numbers.

    Parameters:
        with_disabled_user (bool, optional): Also add a disabled user with the role.

    Returns:
        None
    """
    for role in (ROLE, OTHER_ROLE):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)

    _make_user("wa_one@example.com", "9876543210", [ROLE])
    _make_user("wa_two@example.com", "+91 98765 43211", [ROLE, OTHER_ROLE])
    _make_user("wa_nophone@example.com", None, [ROLE])
    if with_disabled_user:
        _make_user("wa_disabled@example.com", "9876543212", [ROLE], enabled=0)

    frappe.db.commit()  # nosemgrep: frappe-manual-commit -- test fixture setup


def _make_user(email, mobile_no, roles, enabled=1):
    """
    Create a user with a mobile number and roles, replacing any old copy.

    Parameters:
        email (str, required): User email.
        mobile_no (str, optional): Mobile number.
        roles (list, required): Role names.
        enabled (int, optional): 0 for a disabled user. Defaults to 1.

    Returns:
        Document: The User.
    """
    if frappe.db.exists("User", email):
        frappe.delete_doc("User", email, force=True, ignore_permissions=True)

    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": email.split("@")[0],
            "mobile_no": mobile_no,
            "enabled": enabled,
            "roles": [{"role": r} for r in roles],
        }
    )
    user.insert(ignore_permissions=True)
    return user


class TestGetUsersForRoles(IntegrationTestCase):
    """Tests for role -> user resolution."""

    @classmethod
    def setUpClass(cls):
        """Create the roles and users once for the class."""
        super().setUpClass()
        make_role_users(with_disabled_user=True)

    def test_returns_users_with_role(self):
        """Users holding the role are returned."""
        users = get_users_for_roles([ROLE])
        self.assertIn("wa_one@example.com", users)
        self.assertIn("wa_two@example.com", users)

    def test_excludes_disabled_users(self):
        """Disabled users are left out."""
        self.assertNotIn("wa_disabled@example.com", get_users_for_roles([ROLE]))

    def test_excludes_builtin_accounts(self):
        """Administrator and Guest are never returned."""
        users = get_users_for_roles([ROLE, "System Manager"])
        self.assertNotIn("Administrator", users)
        self.assertNotIn("Guest", users)

    def test_user_with_two_matching_roles_listed_once(self):
        """A user with two matching roles appears once."""
        users = get_users_for_roles([ROLE, OTHER_ROLE])
        self.assertEqual(users.count("wa_two@example.com"), 1)

    def test_empty_roles_returns_empty(self):
        """No roles gives no users."""
        self.assertEqual(get_users_for_roles([]), [])
        self.assertEqual(get_users_for_roles(None), [])

    def test_unknown_role_returns_empty(self):
        """A role nobody has gives no users."""
        self.assertEqual(get_users_for_roles(["_Test WA Nonexistent Role"]), [])


class TestGetRoleRecipients(IntegrationTestCase):
    """Tests for end-to-end recipient resolution."""

    @classmethod
    def setUpClass(cls):
        """Create the roles and users once for the class."""
        super().setUpClass()
        make_role_users()

    def _notification(self, rows):
        """
        A notification-like dict with the given recipient rows.

        Parameters:
            rows (list, required): Recipient row dicts.

        Returns:
            frappe._dict: Notification stand-in.
        """
        return frappe._dict(
            name="_Test WA Notification",
            recipients=[frappe._dict(r) for r in rows],
        )

    def test_no_rows_returns_empty(self):
        """A notification without role rows has no recipients."""
        recipients, skipped = get_role_recipients(frappe._dict(name="x", recipients=[]))
        self.assertEqual(recipients, [])
        self.assertEqual(skipped, [])

    def test_resolves_and_normalizes(self):
        """Numbers are found for the role and normalized with the country code."""
        recipients, _ = get_role_recipients(self._notification([{"receiver_by_role": ROLE}]))
        phones = [r["phone"] for r in recipients]
        self.assertIn("919876543210", phones)
        self.assertIn("919876543211", phones)

    def test_user_without_number_is_skipped_not_raised(self):
        """A user without a number is reported as skipped, not an error."""
        recipients, skipped = get_role_recipients(self._notification([{"receiver_by_role": ROLE}]))
        self.assertNotIn("wa_nophone@example.com", [r["user"] for r in recipients])
        self.assertIn("wa_nophone@example.com", [s["user"] for s in skipped])

    def test_two_matching_roles_sends_once(self):
        """A user in two matching roles gets one message."""
        recipients, _ = get_role_recipients(
            self._notification(
                [{"receiver_by_role": ROLE}, {"receiver_by_role": OTHER_ROLE}]
            )
        )
        phones = [r["phone"] for r in recipients]
        self.assertEqual(len(phones), len(set(phones)))
        self.assertEqual(phones.count("919876543211"), 1)

    def test_row_condition_filters(self):
        """A row whose condition is false adds nobody."""
        doc = frappe.get_doc({"doctype": "User", "name": "Administrator"})
        rows = [{"receiver_by_role": ROLE, "condition": "doc.name == 'nobody'"}]
        recipients, _ = get_role_recipients(self._notification(rows), doc=doc)
        self.assertEqual(recipients, [])

    def test_row_condition_skipped_without_doc(self):
        # Scheduler events have no document, so conditional rows cannot apply.
        """Conditional rows are skipped when there is no document."""
        rows = [{"receiver_by_role": ROLE, "condition": "doc.name == 'x'"}]
        recipients, _ = get_role_recipients(self._notification(rows), doc=None)
        self.assertEqual(recipients, [])

    def test_bad_condition_is_logged_not_raised(self):
        """A broken condition is logged and the row skipped."""
        doc = frappe.get_doc({"doctype": "User", "name": "Administrator"})
        rows = [{"receiver_by_role": ROLE, "condition": "doc.no_such_field.boom"}]
        recipients, _ = get_role_recipients(self._notification(rows), doc=doc)
        self.assertEqual(recipients, [])
