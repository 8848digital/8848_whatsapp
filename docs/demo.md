<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->
# Frappe WhatsApp Demo Guide

A step-by-step script for showing Frappe WhatsApp on a Meta test number, from
setup to two-way chat, automatic alerts and bulk campaigns. Plan about 30
minutes; setup (section 1) can be done before the audience joins.

## 1. Before the demo

### What you need

| Item | Where it comes from |
| ---- | ------------------- |
| Facebook / Meta login with access to the company's Meta app | Ask the Business admin to add you under App Roles |
| Meta **test number** (`+1 555 ...`) and its **Phone number ID** | Meta app → WhatsApp → API Setup → "From" |
| **WhatsApp Business Account ID** of the test number | Same page (the test number has its own test WABA) |
| **Access token** | Same page → "Generate access token" (valid 24 hours) or a System User token (does not expire) |
| Phone(s) for the audience to receive messages | Add each one under API Setup → "To" and verify the code (max 5) |
| A public HTTPS URL for the site, for incoming messages | `cloudflared tunnel --url http://localhost:8000 --http-host-header <site>` |

A test number only delivers to numbers verified in the "To" list. Verify the
demo phones a day ahead, not during the demo.

### Set up the account

1. Open `/app/whatsapp-account/new` and fill in:

   | Field | Value |
   | ----- | ----- |
   | Account Name | Meta Test |
   | Token | The access token |
   | URL | `https://graph.facebook.com` (no trailing `/`) |
   | Version | The version shown in API Setup's sample request, e.g. `v25.0` |
   | Phone ID | Phone number ID |
   | Business ID | WhatsApp Business Account ID |
   | App ID | Meta app → App Settings → Basic |
   | Webhook Verify Token | Any string you choose, e.g. `wa_demo_2026` |
   | Status | Active |
   | Is Default Outgoing / Incoming | Ticked |

2. Click **Subscribe App to Webhooks** on the saved account.
3. In Meta → WhatsApp → Configuration → Webhook, set:
   - Callback URL: `https://<public-url>/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.webhook.webhook`
   - Verify token: the string from step 1
   - Webhook fields: subscribe to `messages`
4. Open `/app/whatsapp-templates` and click **Sync from Meta**. The test account
   brings `hello_world` and any templates you created on Meta.

### Dry run

Send `hello_world` (section 2.1) to one demo phone and reply "hi" from it. If
both arrive, the setup is complete.

## 2. Demo script

### 2.1 Send a template

**Shows:** ERPNext talks to Meta directly, no third-party provider.

1. `/app/whatsapp-message/new`
2. Type: Outgoing, To: `91XXXXXXXXXX` (country code, no `+`)
3. Tick **Use Template**, pick `hello_world-en_US`, save.
4. The message arrives on the phone; the record now holds Meta's message id.

### 2.2 Two-way chat

**Shows:** replies land in ERPNext, and free text works inside the 24-hour window.

1. Reply "hi" from the phone.
2. Open `/app/whatsapp-message`: the reply is there with Type = Incoming.
3. Open it and click **Reply**, type a text message, save. It arrives on the phone.
4. Point out the status moving to sent, delivered and read as the phone opens it.

### 2.3 Send from any document

**Shows:** sales and support teams message customers from the record they are on.

1. Open a Sales Order (or any document).
2. Menu (⋯) → **Send To Whatsapp**.
3. Pick a template, pick a Contact (its mobile fills in), click **Send**.
4. A comment is added to the document's timeline with the number and template.

### 2.4 Automatic alert on submit

**Shows:** alerts go out with no one clicking anything.

1. `/app/whatsapp-notification/new`
   - Reference DocType: Sales Order
   - Notification Type: DocType Event, Event: After Submit
   - Template: a template whose `{{1}}` is the order number
   - Field Name: the field holding the customer's mobile
   - Condition (optional): `doc.grand_total > 0`
2. On the template, set **Field Names** to `name` so `{{1}}` is filled with the
   order number.
3. Submit a Sales Order; the customer's phone receives the message.

To show role-based alerts, add a row under **Recipients** with a role (e.g.
Sales Manager). Everyone holding it is messaged in the background, using the
number source set in WhatsApp Settings.

### 2.5 Bulk campaign

**Shows:** one template to many people, with progress and retry.

1. Create a **WhatsApp Recipient List** and add the demo phones (or import
   them from Customers with **Import**).
2. Create a **Bulk WhatsApp Message**: Recipient Type = Recipient List, pick the
   list and a template, submit.
3. Click **Check Progress** for sent, failed and queued counts.
4. Open the **Bulk WhatsApp Status** report for delivered and read counts.

### 2.6 WhatsApp Flow (optional)

**Shows:** a form filled inside WhatsApp, with answers saved in ERPNext.

1. Open a WhatsApp Flow with at least one screen and fields, then
   **Actions → Create on WhatsApp → Upload Flow JSON**.
2. **Send Test** to a demo phone; fill the form on the phone.
3. The answers come back as an incoming WhatsApp Message (`flow_response`).

## 3. If something goes wrong

| Message | Cause | Fix |
| ------- | ----- | --- |
| `(#131030) Recipient phone number not in allowed list` | Number not verified on the test number, or typed without `91` | Verify it under API Setup → To; type the full number |
| `(#133010) Account not registered` | Phone ID belongs to a number that isn't registered on Cloud API | Use the test number's Phone ID, or register the number in WhatsApp Manager |
| `401` / token expired | The 24-hour token ran out | Generate a new token and paste it into the account's Token field |
| Webhook "couldn't be validated" | Wrong callback path, verify token mismatch, or the tunnel restarted | Use the full `api.v1.webhook.webhook` path above; check the token; update the URL after a tunnel restart |
| Templates list empty after sync | Account not Active, or wrong Business ID | Fix the account, then Sync from Meta again |
| Free text not delivered | More than 24 hours since the customer's last message | Send a template instead |

Every webhook call and send result is logged in **WhatsApp Notification Log**,
and errors in **Error Log**.

## 4. After the demo

- Remove the demo phones from the test number's "To" list if they are not
  needed again.
- Revoke or let expire any temporary token; never leave one in code or chat.
- Stop the tunnel. A new tunnel gets a new URL, so the Meta callback URL and
  the site's `host_name` must be updated next time.
