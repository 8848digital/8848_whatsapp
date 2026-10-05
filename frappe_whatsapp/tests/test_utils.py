# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, Shridhar Patil and Contributors
# See license.txt

"""Phone number, template parameter and account lookup helpers."""

from frappe_whatsapp.tests.helpers import IntegrationTestCase, make_test_account, use_test_account
from frappe_whatsapp.utils import (
    format_number,
    get_whatsapp_account,
    normalize_number,
    sanitize_param,
)


class TestFormatNumber(IntegrationTestCase):
    """Tests for format_number utility."""

    def test_strips_leading_plus(self):
        """A leading + is removed."""
        self.assertEqual(format_number("+919900112233"), "919900112233")

    def test_no_plus_unchanged(self):
        """A number without + is returned as is."""
        self.assertEqual(format_number("919900112233"), "919900112233")

    def test_plus_only_at_start(self):
        """Only the leading + matters; the digits stay the same."""
        self.assertEqual(format_number("+1234567890"), "1234567890")


class TestNormalizeNumber(IntegrationTestCase):
    """Tests for normalize_number utility."""

    def test_strips_formatting(self):
        """Spaces, dashes, brackets and + are removed."""
        self.assertEqual(normalize_number("+91 98765-43210"), "919876543210")
        self.assertEqual(normalize_number("(91) 98765 43210"), "919876543210")

    def test_already_normalized_unchanged(self):
        """A clean international number is returned as is."""
        self.assertEqual(normalize_number("919876543210"), "919876543210")

    def test_adds_country_code_to_national_number(self):
        """A 10-digit number gets the given country code."""
        self.assertEqual(normalize_number("9876543210", "91"), "919876543210")

    def test_national_number_without_country_code_is_rejected(self):
        # Meta rejects these, so skip rather than send a doomed request.
        """A 10-digit number with no country code to add is rejected."""
        self.assertIsNone(normalize_number("9876543210"))

    def test_strips_trunk_and_international_prefix(self):
        """A leading 0 or 00 is dropped."""
        self.assertEqual(normalize_number("09876543210", "91"), "919876543210")
        self.assertEqual(normalize_number("00919876543210"), "919876543210")

    def test_rejects_unusable_values(self):
        """Empty, short and non-numeric values give None."""
        for value in (None, "", "12345", "not a number", "0000"):
            with self.subTest(value=value):
                self.assertIsNone(normalize_number(value, "91"))

    def test_rejects_over_e164_length(self):
        """Numbers longer than 15 digits give None."""
        self.assertIsNone(normalize_number("9" * 16))


class TestSanitizeParam(IntegrationTestCase):
    """Tests for sanitize_param utility."""

    def test_strips_text_editor_markup(self):
        # What Holiday.description actually yields from get_formatted().
        """HTML from text editor fields is stripped."""
        self.assertEqual(
            sanitize_param("<div class='ql-snow'>Mahatma Gandhi Jayanti</div>"),
            "Mahatma Gandhi Jayanti",
        )

    def test_collapses_whitespace(self):
        # Meta rejects newlines, tabs and runs of four or more spaces.
        """Newlines, tabs and long runs of spaces become single spaces."""
        self.assertEqual(sanitize_param("Line one\nLine\ttwo    end"), "Line one Line two end")

    def test_unescapes_entities(self):
        """HTML entities like &amp; are turned back into characters."""
        self.assertEqual(sanitize_param("<p>Sales &amp; Stock</p>"), "Sales & Stock")

    def test_plain_value_unchanged(self):
        """Plain text is returned as is."""
        self.assertEqual(sanitize_param("REPUBLIC DAY"), "REPUBLIC DAY")

    def test_none_becomes_empty_string(self):
        """None gives an empty string."""
        self.assertEqual(sanitize_param(None), "")

    def test_truncates_to_meta_limit(self):
        """Long values are cut to Meta's 1024 character limit, ending in ..."""
        result = sanitize_param("x" * 2000)
        self.assertEqual(len(result), 1024)
        self.assertTrue(result.endswith("..."))


class TestGetWhatsAppAccount(IntegrationTestCase):
    """Tests for get_whatsapp_account utility."""

    @classmethod
    def setUpClass(cls):
        """Create the shared test records once for the class."""
        super().setUpClass()
        make_test_account("Test Utils Account", "utils_test")

    def setUp(self):
        """Make the utils test account the default for this test."""
        use_test_account("Test Utils Account")

    def test_get_account_by_phone_id(self):
        """Test getting account by phone_id."""
        account = get_whatsapp_account(phone_id="utils_test_phone_id")
        self.assertIsNotNone(account)
        self.assertEqual(account.name, "Test Utils Account")

    def test_get_account_by_phone_id_not_found(self):
        """Test getting account by non-existent phone_id falls back to default."""
        account = get_whatsapp_account(phone_id="nonexistent_phone_id")
        # Should fall back to default incoming
        if account:
            self.assertTrue(account.is_default_incoming)

    def test_get_default_incoming_account(self):
        """Test getting default incoming account."""
        account = get_whatsapp_account(account_type='incoming')
        self.assertIsNotNone(account)
        self.assertEqual(account.is_default_incoming, 1)

    def test_get_default_outgoing_account(self):
        """Test getting default outgoing account."""
        account = get_whatsapp_account(account_type='outgoing')
        self.assertIsNotNone(account)
        self.assertEqual(account.is_default_outgoing, 1)
