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
# SETUP.md

## Meta WhatsApp Cloud API

### Overview

All sending, receiving, templates, flows and media go straight to Meta's
WhatsApp Cloud (Graph) API. Each WhatsApp Business phone number is one
**WhatsApp Account** record.

### Required Credentials

| Credential | Where it's stored | Required? |
| ---------- | ----------------- | --------- |
| Access Token (permanent system-user token) | WhatsApp Account → `token` (Password) | Yes |
| Phone Number ID | WhatsApp Account → `phone_id` | Yes |
| WhatsApp Business Account ID | WhatsApp Account → `business_id` | Yes |
| App ID | WhatsApp Account → `app_id` | Yes, for template media headers |
| Webhook Verify Token (any secret string you choose) | WhatsApp Account → `webhook_verify_token` | Yes, to receive messages |

Get these from the [Meta Developer Portal](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
→ your app → WhatsApp → API Setup. Never paste the token anywhere except the
Access Token field.

### Settings DocType Fields

**WhatsApp Account** (one per phone number):

| Field | Type | Mandatory | Notes |
| ----- | ---- | --------- | ----- |
| Account Name | Data | Yes | Any label, e.g. "Sales WhatsApp". |
| Access Token | Password | Yes | See above. |
| URL | Data | Yes | `https://graph.facebook.com` |
| Version | Data | Yes | Graph API version, e.g. `v19.0`. |
| Phone ID | Data | Yes | Phone Number ID from Meta. |
| Business ID | Data | Yes | WhatsApp Business Account ID. |
| App ID | Data | For media templates | Needed to upload sample images/documents. |
| Webhook Verify Token | Data | To receive messages | Must match what you enter in Meta's webhook settings. |
| Status | Select | Yes | Only Active accounts are used when syncing templates. |
| Is Default Incoming / Is Default Outgoing | Check | One account each | Used when a message or notification has no account set. |
| Allow Auto Read Receipt | Check | No | Mark incoming messages as read automatically. |

**WhatsApp Settings** (single):

| Field | Type | Mandatory | Notes |
| ----- | ---- | --------- | ----- |
| Default Incoming / Outgoing Account | Link | No | Kept in sync by the migration patch. |
| Role Phone Source | Select | No | For "Recipients by Role": use User Mobile No, Employee Cell Number, or one then the other. Default: User, then Employee. |
| Default Country Code | Data | No | Added to 10-digit numbers found on Users/Employees, e.g. `91`. |

### Site Config / Environment Variables

None. Everything is configured in the DocTypes above. The site must be
reachable over **https** from the internet so Meta can call the webhook and
download attachments.

### Webhooks

Register in Meta's App Dashboard → WhatsApp → Configuration:

| What | URL on your site |
| ---- | ---------------- |
| Webhook (messages, statuses, template approvals) | `https://<your-site>/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.webhook.webhook` |
| Flow data endpoint (only for flows that use an endpoint) | `https://<your-site>/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow_endpoint.handle_flow_request` |

- Verify token: the **Webhook Verify Token** of the WhatsApp Account.
- Subscribe to the `messages` and `message_template_status_update` webhook fields.
- Then open the WhatsApp Account and click **Subscribe App to Webhooks** (needed once per business account).
- The old URLs (`/api/method/frappe_whatsapp.utils.webhook.webhook` and
  `/api/method/frappe_whatsapp.frappe_whatsapp.api.flow_endpoint.handle_flow_request`)
  still work, so existing Meta configurations don't need changing.

### How to Test

1. WhatsApp Templates list → **Sync from Meta**: your approved templates appear.
2. Create a WhatsApp Message (Outgoing, content type Text) to a number allowed in Meta's test settings; status becomes Success.
3. Send a WhatsApp message to the business number; a new Incoming WhatsApp Message appears, and an entry is added to WhatsApp Notification Log.
