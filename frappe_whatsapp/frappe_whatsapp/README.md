<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->
<!--
Copyright (c) 2026, Shridhar Patil and contributors
For license information, please see license.txt
-->
# Frappe Whatsapp

## Purpose

Owns everything WhatsApp: accounts, messages, templates, notifications, flows
and bulk campaigns, talking to Meta's Cloud API. The module keeps the name
`frappe_whatsapp` (same as the app) because renaming it would change every
import path and DocType module on sites already running the app.

## Layout

| Path | What lives there |
| ---- | ---------------- |
| `api/v1/` | Every whitelisted endpoint, as thin wrappers: `webhook.py`, `flow_endpoint.py` (called by Meta), `message.py`, `template.py`, `account.py`, `notification.py`, `flow.py`, `bulk_messaging.py`. Old endpoint paths are mapped here by `override_whitelisted_methods` in `hooks.py`. |
| `doctype/<name>/<name>.py` | Controllers: hook methods only, delegating to the files next to them. |
| `doctype/<name>/*.py` | The logic, one file per job (e.g. `message_payload.py`, `notification_sender.py`, `flow_builder.py`). |
| `tasks.py` | Scheduler targets (notifications by frequency, date-based notifications) and background jobs (role notifications). |
| `notification_events.py` | The `doc_events["*"]` hook that fires DocType Event notifications. |

## DocTypes

| DocType | Purpose |
| ------- | ------- |
| WhatsApp Account | Phone number + Meta credentials; default incoming/outgoing flags (`account_utils.py`). |
| WhatsApp Settings | Default accounts and role phone-number source (single). |
| WhatsApp Message | Sent/received messages; payload builders in `message_payload.py` / `template_payload.py`, sending in `message_utils.py`. |
| WhatsApp Message Fields | Child: document field mapped to a template parameter. |
| WhatsApp Templates | Templates synced with Meta (`template_meta.py` create/update/delete, `template_media.py` sample upload, `template_fetch.py` pull). |
| WhatsApp Button | Child: one template button. |
| WhatsApp Notification | Send rules: `notification_validation.py`, `notification_payload.py`, `notification_sender.py` (who and when), `notification_delivery.py` (post, save, log), `notification_schedule.py`, `notification_recipients.py` (roles), `recipient_phone.py` (User/Employee number). |
| WhatsApp Notification Recipient | Child: role (and condition) to notify. |
| WhatsApp Notification Log | Raw webhook/send log. |
| WhatsApp Flow | Flows: `flow_builder.py`/`flow_components.py`/`flow_screens.py` (Flow JSON), `flow_meta.py` (create/publish/...), `flow_status.py`, `flow_import.py`/`flow_rows.py`, `flow_graph.py`, `flow_data_exchange.py`. |
| WhatsApp Flow Screen | Child: one flow screen. |
| WhatsApp Flow Field | Child: one component on a screen. |
| Bulk WhatsApp Message | Campaigns: `bulk_utils.py` (check, queue, send), `bulk_progress.py` (progress, retry), `bulk_status.py`. |
| WhatsApp Recipient List | Reusable recipient lists; `recipient_import.py` imports from any DocType. |
| WhatsApp Recipient | Child: one recipient with its variables. |
| WhatsApp Profiles | Contacts seen in chats (`profile_utils.py`). |
| WhatsApp Report Sender | PDF of a print format or report for WhatsApp (`report_pdf.py`). |

## Reports

- **Bulk WhatsApp Status** — each submitted bulk message with sent, delivered, read and failed counts.
