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
# Frappe WhatsApp

## Overview

WhatsApp for Frappe/ERPNext using Meta's WhatsApp Cloud API directly, with no
third-party provider in between. Teams use it to message customers from any
document, send automatic alerts (invoice submitted, payment due, OTPs), run
bulk campaigns, collect form answers through WhatsApp Flows, and keep every
conversation in ERPNext. This is 8848 Digital's fork of
[shridarpatil/frappe_whatsapp](https://github.com/shridarpatil/frappe_whatsapp)
([upstream documentation](https://shridarpatil.github.io/frappe_whatsapp/)).

## Key DocTypes

| DocType | Owned by this app? | Purpose |
| ------- | ------------------ | ------- |
| WhatsApp Account | Yes | A WhatsApp Business phone number and its Meta credentials; one can be the default for incoming and outgoing messages. |
| WhatsApp Settings | Yes | Site-wide defaults: default accounts, and where role recipients' phone numbers come from. |
| WhatsApp Message | Yes | Every message sent or received, with delivery status (sent, delivered, read). |
| WhatsApp Templates | Yes | Message templates, created here and submitted to Meta for approval, or pulled from Meta. |
| WhatsApp Notification | Yes | A rule that sends a template when a document event happens, on a date, or on a schedule. |
| WhatsApp Flow | Yes | An in-chat form (screens and fields) published to WhatsApp; answers come back as messages. |
| Bulk WhatsApp Message | Yes | One template sent to many recipients in the background, with progress and retry. |
| WhatsApp Recipient List | Yes | A reusable list of numbers, imported from any DocType, with per-person variables. |
| WhatsApp Profiles | Yes | Contacts seen in conversations (number and WhatsApp profile name). |
| WhatsApp Report Sender | Yes | Turns a print format or a report into a PDF that can be sent on WhatsApp. |
| WhatsApp Notification Log | Yes | Raw log of webhook events and send results, for troubleshooting. |

## Features

- Connect several WhatsApp Business numbers and choose which one sends or receives by default.
- Chat two-way: incoming texts, replies, reactions, button and list answers, orders, images, audio, video and documents are saved as WhatsApp Messages.
- Send free-form messages within Meta's 24-hour window: text, media, reactions, reply buttons (up to 3) and option lists (up to 10).
- Create templates (text/image/document headers, footers, quick-reply, website, phone, OTP copy-code, catalog and multi-product buttons) and sync them with Meta.
- Send a template from any document with the "Send To Whatsapp" menu option.
- Automatic notifications on document events (insert, save, submit, cancel, delete...), on dates (days before/after a date field) or on a schedule (hourly to monthly), with conditions, document print or file attachments, and a field set after sending.
- Notify people by role: everyone holding a role is messaged, using their User or Employee number, in the background.
- Bulk campaigns from a recipient list or typed numbers, with common or per-recipient template values, product messages, a progress bar and one-click retry of failed messages.
- Build WhatsApp Flows (forms) screen by screen, publish them, send a test, and import or sync existing flows from Meta.
- Automatic read receipts (blue ticks) per account, or a "Mark as read" button.
- Turn a print format or report into a PDF ready to send on WhatsApp.
- Bulk WhatsApp Status report: delivered, read and failed counts per campaign.

## Integrations

- **Meta WhatsApp Cloud API** (messages, templates, flows, media, webhooks) — see [SETUP.md](./SETUP.md#meta-whatsapp-cloud-api)

## Installation

    bench get-app frappe_whatsapp https://github.com/8848digital/8848_whatsapp
    bench --site <site_name> install-app frappe_whatsapp
    bench --site <site_name> migrate

Then follow [SETUP.md](./SETUP.md) to connect a WhatsApp number.

## App Structure

See [frappe_whatsapp/frappe_whatsapp/README.md](./frappe_whatsapp/frappe_whatsapp/README.md) for the module
layout. The app follows the 8848 Digital skills conventions: whitelisted endpoints only under
`frappe_whatsapp/frappe_whatsapp/api/v1/`, thin DocType controllers with their logic in sibling
files, scheduler and background jobs in `tasks.py`, and shared helpers in `utils/`.

API responses from `/api/method/frappe_whatsapp...` use the standard envelope
`{"status", "status_code", "message", "data", "errors"}`; the payload is in `data`. The two
endpoints Meta calls (the webhook and the Flow endpoint) are left in Meta's own format. In Desk
code, call these endpoints with `frappe_whatsapp.call(...)`, which passes `data` to the
callback and shows `message` when a call fails.

## Maintainers

8848 Digital (fork maintainers). Original app by Shridhar Patil and contributors.

## License

Proprietary — Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Based on Frappe WhatsApp by Shridhar Patil, whose MIT license notice is kept
in [license.txt](license.txt) as that license requires.
