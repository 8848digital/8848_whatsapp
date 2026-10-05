# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""WhatsApp Flow validation, and the Flow endpoint's health check."""

import frappe

from frappe_whatsapp.tests.flow_case import FlowTestCase


class TestWhatsAppFlowValidation(FlowTestCase):
    """Screen rules a flow must follow before it can be saved."""

    def test_validation_requires_screen(self):
        """Test that flow validation requires at least one screen."""
        with self.assertRaises(frappe.ValidationError):
            flow = frappe.get_doc({
                "doctype": "WhatsApp Flow",
                "flow_name": "Test No Screens",
                "whatsapp_account": "Test Account",
                "category": "OTHER",
                "screens": [],
                "fields": []
            })
            flow.insert(ignore_permissions=True)

    def test_validation_requires_terminal_screen(self):
        """Test that flow validation requires at least one terminal screen."""
        with self.assertRaises(frappe.ValidationError):
            flow = frappe.get_doc({
                "doctype": "WhatsApp Flow",
                "flow_name": "Test No Terminal",
                "whatsapp_account": "Test Account",
                "category": "OTHER",
                "screens": [{"screen_id": "s1", "screen_title": "Screen 1", "terminal": 0}],
                "fields": []
            })
            flow.insert(ignore_permissions=True)

    def test_validation_duplicate_screen_ids(self):
        """Test that flow validation catches duplicate screen IDs."""
        with self.assertRaises(frappe.ValidationError):
            flow = frappe.get_doc({
                "doctype": "WhatsApp Flow",
                "flow_name": "Test Duplicate",
                "whatsapp_account": "Test Account",
                "category": "OTHER",
                "screens": [
                    {"screen_id": "same", "screen_title": "Screen 1", "terminal": 0},
                    {"screen_id": "same", "screen_title": "Screen 2", "terminal": 1}
                ],
                "fields": []
            })
            flow.insert(ignore_permissions=True)


class TestFlowEndpoint(FlowTestCase):
    """Test cases for flow endpoint handler."""

    def test_health_check(self):
        """Test endpoint health check response."""
        from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_data_exchange import handle_flow_request

        response = handle_flow_request("POST", {"action": "INIT", "screen": "INIT"})
        self.assertIn("screen", response)
        self.assertIn("data", response)

        self.assertEqual(handle_flow_request("GET", None), {"status": "ok"})
        self.assertEqual(handle_flow_request("POST", {"action": "ping"}), {"data": {"status": "active"}})
