# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Shared setup for the WhatsApp Flow tests."""

import frappe

from frappe_whatsapp.tests.helpers import IntegrationTestCase, make_test_account


class FlowTestCase(IntegrationTestCase):
    """Test account and a flow factory. Has no tests itself."""

    def setUp(self):
        """Set up test data."""
        make_test_account("Test Account", "flow_test", token="test_token")

    def tearDown(self):
        """Clean up test data."""
        # Delete test flows
        for flow in frappe.get_all("WhatsApp Flow", filters={"flow_name": ["like", "Test%"]}):
            frappe.delete_doc("WhatsApp Flow", flow.name, force=True)

    def create_test_flow(self, flow_name, screens_data, fields_data):
        """Insert a flow for the test."""
        flow = frappe.get_doc({
            "doctype": "WhatsApp Flow",
            "flow_name": flow_name,
            "whatsapp_account": "Test Account",
            "category": "OTHER",
            "data_api_version": "7.3",
            "screens": screens_data,
            "fields": fields_data
        })
        flow.insert(ignore_permissions=True)
        return flow
