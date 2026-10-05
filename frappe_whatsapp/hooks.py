# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2022, Shridhar Patil and contributors
# For license information, please see license.txt

from . import __version__ as app_version

app_name = "frappe_whatsapp"
app_title = "Frappe Whatsapp"
app_publisher = "Shridhar Patil"
app_description = "WhatsApp integration for frappe"
app_email = "shridhar.p@zerodha.com"
app_license = "MIT"

# Desk-wide script: the "Send To Whatsapp" menu option on every form.
app_include_js = "/assets/frappe_whatsapp/js/frappe_whatsapp.js"

_TASKS = "frappe_whatsapp.frappe_whatsapp.tasks"

scheduler_events = {
	"all": [f"{_TASKS}.send_all_frequency_notifications"],
	"hourly": [f"{_TASKS}.send_hourly_notifications"],
	"hourly_long": [f"{_TASKS}.send_hourly_long_notifications"],
	"daily": [
		f"{_TASKS}.send_daily_notifications",
		f"{_TASKS}.send_date_based_notifications",
	],
	"daily_long": [f"{_TASKS}.send_daily_long_notifications"],
	"weekly": [f"{_TASKS}.send_weekly_notifications"],
	"weekly_long": [f"{_TASKS}.send_weekly_long_notifications"],
	"monthly": [f"{_TASKS}.send_monthly_notifications"],
	"monthly_long": [f"{_TASKS}.send_monthly_long_notifications"],
}

# WhatsApp Notifications can watch any DocType, so every document event is checked.
# (Helper names start with "_" so Frappe does not read them as hooks.)
_NOTIFICATION_EVENT = "frappe_whatsapp.frappe_whatsapp.notification_events.run_notifications_for_doc_event"
doc_events = {
	"*": {
		"before_insert": _NOTIFICATION_EVENT,
		"after_insert": _NOTIFICATION_EVENT,
		"before_validate": _NOTIFICATION_EVENT,
		"validate": _NOTIFICATION_EVENT,
		"on_update": _NOTIFICATION_EVENT,
		"before_submit": _NOTIFICATION_EVENT,
		"on_submit": _NOTIFICATION_EVENT,
		"before_cancel": _NOTIFICATION_EVENT,
		"on_cancel": _NOTIFICATION_EVENT,
		"on_trash": _NOTIFICATION_EVENT,
		"after_delete": _NOTIFICATION_EVENT,
		"before_update_after_submit": _NOTIFICATION_EVENT,
		"on_update_after_submit": _NOTIFICATION_EVENT,
	}
}

# Endpoints moved to frappe_whatsapp.frappe_whatsapp.api.v1. The old paths keep
# working because Meta (webhook, flow endpoint) and other apps may still call them.
_API = "frappe_whatsapp.frappe_whatsapp.api.v1"
override_whitelisted_methods = {
	"frappe_whatsapp.utils.webhook.webhook": f"{_API}.webhook.webhook",
	"frappe_whatsapp.frappe_whatsapp.api.flow_endpoint.handle_flow_request": f"{_API}.flow_endpoint.handle_flow_request",
	"frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message.whatsapp_message.send_template": f"{_API}.message.send_template",
	"frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.whatsapp_templates.fetch": f"{_API}.template.fetch",
	"frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.whatsapp_notification.call_trigger_notifications": f"{_API}.notification.call_trigger_notifications",
	"frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.whatsapp_flow.get_whatsapp_flows": f"{_API}.flow.get_whatsapp_flows",
	"frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.whatsapp_flow.import_flow_from_whatsapp": f"{_API}.flow.import_flow_from_whatsapp",
	"frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.whatsapp_flow.sync_all_flows": f"{_API}.flow.sync_all_flows",
	"frappe_whatsapp.utils.bulk_messaging.get_progress": f"{_API}.bulk_messaging.get_progress",
	"frappe_whatsapp.utils.bulk_messaging.retry_failed": f"{_API}.bulk_messaging.retry_failed",
	"frappe_whatsapp.utils.bulk_messaging.import_recipients": f"{_API}.bulk_messaging.import_recipients",
}

# Wraps frappe_whatsapp API responses in the standard envelope (Meta callbacks are skipped).
after_request = ["frappe_whatsapp.utils.api_handlers.response_formatter.format_frappe_response_to_custom"]

# Fixtures exported with `bench --site <site> 8848-export-fixtures` (see commands/README.md).
custom_fixtures = []
commands = ["frappe_whatsapp.commands.export_fixtures.export_fixtures"]
