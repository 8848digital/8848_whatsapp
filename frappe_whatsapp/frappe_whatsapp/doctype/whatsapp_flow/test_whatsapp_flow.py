# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2025, Shridhar Patil and contributors
# For license information, please see license.txt

"""Flow JSON built from a WhatsApp Flow's screens and fields."""

import json

from frappe_whatsapp.tests.flow_case import FlowTestCase


class TestWhatsAppFlow(FlowTestCase):
    """Test cases for WhatsApp Flow feature."""

    def test_single_screen_flow_json_generation(self):
        """Test flow JSON generation for a single screen flow."""
        screens = [{
            "screen_id": "WELCOME",
            "screen_title": "Welcome",
            "terminal": 1
        }]
        fields = [{
            "screen": "WELCOME",
            "field_name": "user_name",
            "field_type": "TextInput",
            "label": "Your Name",
            "required": 1,
            "enabled": 1
        }]

        flow = self.create_test_flow("Test Single Screen", screens, fields)
        flow_json = json.loads(flow.flow_json)

        # Verify structure
        self.assertEqual(flow_json["version"], "7.3")
        self.assertEqual(len(flow_json["screens"]), 1)

        # Verify screen
        screen = flow_json["screens"][0]
        self.assertEqual(screen["id"], "WELCOME")
        self.assertEqual(screen["title"], "Welcome")
        self.assertTrue(screen.get("terminal"))
        self.assertTrue(screen.get("success"))

        # Verify no routing_model or data_api_version (client-only flow)
        self.assertNotIn("routing_model", flow_json)
        self.assertNotIn("data_api_version", flow_json)

    def test_multi_screen_flow_json_generation(self):
        """Test flow JSON generation for multi-screen flow."""
        screens = [
            {"screen_id": "contact", "screen_title": "Contact Details", "terminal": 0},
            {"screen_id": "booking", "screen_title": "Booking Details", "terminal": 1}
        ]
        fields = [
            {"screen": "contact", "field_name": "name", "field_type": "TextInput", "label": "Name", "required": 1, "enabled": 1},
            {"screen": "contact", "field_name": "mobile", "field_type": "TextInput", "label": "Mobile", "required": 1, "enabled": 1},
            {"screen": "booking", "field_name": "date", "field_type": "TextInput", "label": "Date", "required": 1, "enabled": 1}
        ]

        flow = self.create_test_flow("Test Multi Screen", screens, fields)
        flow_json = json.loads(flow.flow_json)

        # Verify two screens
        self.assertEqual(len(flow_json["screens"]), 2)

        # First screen should have empty data (no incoming data)
        self.assertEqual(flow_json["screens"][0]["data"], {})

        # Second screen should have data declarations for fields from first screen
        second_screen_data = flow_json["screens"][1]["data"]
        self.assertIn("name", second_screen_data)
        self.assertIn("mobile", second_screen_data)
        self.assertEqual(second_screen_data["name"]["type"], "string")

    def test_navigate_action_payload(self):
        """Test that navigate action includes correct payload."""
        screens = [
            {"screen_id": "screen1", "screen_title": "Screen 1", "terminal": 0},
            {"screen_id": "screen2", "screen_title": "Screen 2", "terminal": 1}
        ]
        fields = [
            {"screen": "screen1", "field_name": "field1", "field_type": "TextInput", "label": "Field 1", "required": 1, "enabled": 1}
        ]

        flow = self.create_test_flow("Test Navigate", screens, fields)
        flow_json = json.loads(flow.flow_json)

        # Find the footer in first screen
        first_screen = flow_json["screens"][0]
        footer = None
        for child in first_screen["layout"]["children"]:
            if child.get("type") == "Footer":
                footer = child
                break

        self.assertIsNotNone(footer)
        action = footer["on-click-action"]
        self.assertEqual(action["name"], "navigate")
        self.assertEqual(action["next"]["name"], "screen2")

        # Payload should reference form fields
        self.assertEqual(action["payload"]["field1"], "${form.field1}")

    def test_complete_action_payload(self):
        """Test that complete action includes all accumulated data."""
        screens = [
            {"screen_id": "screen1", "screen_title": "Screen 1", "terminal": 0},
            {"screen_id": "screen2", "screen_title": "Screen 2", "terminal": 1}
        ]
        fields = [
            {"screen": "screen1", "field_name": "name", "field_type": "TextInput", "label": "Name", "enabled": 1},
            {"screen": "screen2", "field_name": "email", "field_type": "TextInput", "label": "Email", "enabled": 1}
        ]

        flow = self.create_test_flow("Test Complete", screens, fields)
        flow_json = json.loads(flow.flow_json)

        # Find footer in terminal screen
        terminal_screen = flow_json["screens"][1]
        footer = None
        for child in terminal_screen["layout"]["children"]:
            if child.get("type") == "Footer":
                footer = child
                break

        self.assertIsNotNone(footer)
        action = footer["on-click-action"]
        self.assertEqual(action["name"], "complete")

        # Payload should include data from previous screen and form from current
        payload = action["payload"]
        self.assertEqual(payload["name"], "${data.name}")  # From previous screen
        self.assertEqual(payload["email"], "${form.email}")  # From current screen

    def test_text_display_components(self):
        """Test text display components (TextHeading, TextBody, etc.)."""
        screens = [{"screen_id": "info", "screen_title": "Info", "terminal": 1}]
        fields = [
            {"screen": "info", "field_name": "heading", "field_type": "TextHeading", "label": "Welcome!", "enabled": 1},
            {"screen": "info", "field_name": "body", "field_type": "TextBody", "label": "Please fill the form", "enabled": 1}
        ]

        flow = self.create_test_flow("Test Text Components", screens, fields)
        flow_json = json.loads(flow.flow_json)

        children = flow_json["screens"][0]["layout"]["children"]

        # Text components should have type and text properties
        heading = children[0]
        self.assertEqual(heading["type"], "TextHeading")
        self.assertEqual(heading["text"], "Welcome!")

        body = children[1]
        self.assertEqual(body["type"], "TextBody")
        self.assertEqual(body["text"], "Please fill the form")

    def test_dropdown_with_options(self):
        """Test dropdown field with options."""
        screens = [{"screen_id": "select", "screen_title": "Select", "terminal": 1}]
        fields = [{
            "screen": "select",
            "field_name": "country",
            "field_type": "Dropdown",
            "label": "Country",
            "enabled": 1,
            "options": json.dumps([
                {"id": "us", "title": "United States"},
                {"id": "uk", "title": "United Kingdom"},
                {"id": "in", "title": "India"}
            ])
        }]

        flow = self.create_test_flow("Test Dropdown", screens, fields)
        flow_json = json.loads(flow.flow_json)

        children = flow_json["screens"][0]["layout"]["children"]
        dropdown = children[0]

        self.assertEqual(dropdown["type"], "Dropdown")
        self.assertEqual(dropdown["name"], "country")
        self.assertEqual(len(dropdown["data-source"]), 3)
        self.assertEqual(dropdown["data-source"][0]["id"], "us")

    def test_text_input_validation(self):
        """Test text input with min/max chars."""
        screens = [{"screen_id": "form", "screen_title": "Form", "terminal": 1}]
        fields = [{
            "screen": "form",
            "field_name": "phone",
            "field_type": "TextInput",
            "label": "Phone",
            "enabled": 1,
            "min_chars": 10,
            "max_chars": 15,
            "error_message": "Phone must be 10-15 digits"
        }]

        flow = self.create_test_flow("Test Validation", screens, fields)
        flow_json = json.loads(flow.flow_json)

        children = flow_json["screens"][0]["layout"]["children"]
        phone_field = children[0]

        self.assertEqual(phone_field["min-chars"], 10)
        self.assertEqual(phone_field["max-chars"], 15)
        self.assertEqual(phone_field["error-message"], "Phone must be 10-15 digits")

    def test_disabled_fields_excluded(self):
        """Test that disabled fields are not included in flow JSON."""
        screens = [{"screen_id": "form", "screen_title": "Form", "terminal": 1}]
        fields = [
            {"screen": "form", "field_name": "active", "field_type": "TextInput", "label": "Active", "enabled": 1},
            {"screen": "form", "field_name": "disabled", "field_type": "TextInput", "label": "Disabled", "enabled": 0}
        ]

        flow = self.create_test_flow("Test Disabled", screens, fields)
        flow_json = json.loads(flow.flow_json)

        children = flow_json["screens"][0]["layout"]["children"]
        field_names = [c.get("name") for c in children if c.get("name")]

        self.assertIn("active", field_names)
        self.assertNotIn("disabled", field_names)

    def test_client_only_flow_no_endpoint_fields(self):
        """Test that generated JSON is client-only (no endpoint required)."""
        screens = [{"screen_id": "test", "screen_title": "Test", "terminal": 1}]
        fields = [{"screen": "test", "field_name": "f1", "field_type": "TextInput", "label": "F1", "enabled": 1}]

        flow = self.create_test_flow("Test Client Only", screens, fields)
        flow_json = json.loads(flow.flow_json)

        # Client-only flows should NOT have these fields
        self.assertNotIn("routing_model", flow_json)
        self.assertNotIn("data_api_version", flow_json)
        self.assertNotIn("data_channel_uri", flow_json)

        # Should have version and screens
        self.assertIn("version", flow_json)
        self.assertIn("screens", flow_json)
