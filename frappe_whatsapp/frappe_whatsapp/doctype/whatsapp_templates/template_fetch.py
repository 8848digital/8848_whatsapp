# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Pull templates from Meta into WhatsApp Templates."""

import frappe
from frappe.integrations.utils import make_request

from frappe_whatsapp.utils.meta_api import get_auth_headers, get_graph_url, get_meta_error

# Meta button type -> our WhatsApp Button type. An OTP copy-code button is
# stored as "Visit Website" with an otp_type URL (see template_meta.build_button).
BUTTON_TYPES = {
	"URL": "Visit Website",
	"PHONE_NUMBER": "Call Phone",
	"QUICK_REPLY": "Quick Reply",
	"FLOW": "Flow",
	"MPM": "Multi-Product Message",
	"CATALOG": "Catalog",
	"OTP": "Visit Website",
}


def fetch_templates_from_meta():
	"""
	Create or update a WhatsApp Template for every template of every active account.

	Returns:
		str: Success message.
	"""
	accounts = frappe.get_all("WhatsApp Account", filters={"status": "Active"}, pluck="name")
	for account_name in accounts:
		fetch_account_templates(frappe.get_doc("WhatsApp Account", account_name))

	return "Successfully fetched templates from meta"


def fetch_account_templates(account):
	"""
	Fetch one account's templates from Meta and save them locally.

	Parameters:
		account (Document, required): Active WhatsApp Account.

	Returns:
		None
	"""
	try:
		response = make_request(
			"GET",
			get_graph_url(account, f"{account.business_id}/message_templates"),
			headers=get_auth_headers(account),
		)
	except Exception as e:
		throw_fetch_error(e)

	for meta_template in response["data"]:
		save_meta_template(meta_template, account.name)


def save_meta_template(meta_template, account_name):
	"""
	Create or update the local copy of one Meta template.

	Parameters:
		meta_template (dict, required): Template as returned by Meta.
		account_name (str, required): WhatsApp Account it belongs to.

	Returns:
		None
	"""
	if frappe.db.exists("WhatsApp Templates", {"actual_name": meta_template["name"]}):
		template = frappe.get_doc("WhatsApp Templates", {"actual_name": meta_template["name"]})
	else:
		template = frappe.new_doc("WhatsApp Templates")
		template.template_name = meta_template["name"]
		template.actual_name = meta_template["name"]

	template.status = meta_template["status"]
	template.language_code = meta_template["language"]
	template.category = meta_template["category"]
	template.id = meta_template["id"]
	template.whatsapp_account = account_name

	for component in meta_template["components"]:
		apply_component(template, component)

	upsert_without_hooks(template, "WhatsApp Button", "buttons")


def apply_component(template, component):
	"""
	Copy one Meta component (header, footer, body or buttons) onto the template.

	Parameters:
		template (Document, required): Local WhatsApp Templates record.
		component (dict, required): Meta component.

	Returns:
		None
	"""
	if component["type"] == "HEADER":
		template.header_type = component["format"]
		if component["format"] == "TEXT":
			template.header = component["text"]
	elif component["type"] == "FOOTER":
		template.footer = component["text"]
	elif component["type"] == "BODY":
		template.template = component["text"]
		body_examples = (component.get("example") or {}).get("body_text")
		if body_examples:
			template.sample_values = ",".join(body_examples[0])
	elif component["type"] == "BUTTONS":
		template.set("buttons", [])
		frappe.db.delete("WhatsApp Button", {"parent": template.name, "parenttype": "WhatsApp Templates"})
		for sequence, meta_button in enumerate(component.get("buttons", []), start=1):
			button = build_button_row(meta_button, sequence)
			if button:
				template.append("buttons", button)


def build_button_row(meta_button, sequence):
	"""
	WhatsApp Button row values for a Meta button; unknown types are logged and skipped.

	Parameters:
		meta_button (dict, required): Button as returned by Meta.
		sequence (int, required): Position of the button, starting at 1.

	Returns:
		dict | None: Row values, or None for an unknown button type.
	"""
	meta_type = meta_button.get("type")
	if meta_type not in BUTTON_TYPES:
		frappe.log_error("WhatsApp Fetch Error", f"Unknown WhatsApp Button Type: {meta_type}")
		return None

	button = {
		"button_type": BUTTON_TYPES[meta_type],
		"button_label": meta_button.get("text", "Copy code"),
		"sequence": sequence,
	}

	if meta_type == "OTP":
		# Rebuild the OTP URL so build_button recognises it on the next save.
		otp_type = meta_button.get("otp_type", "COPY_CODE")
		button["website_url"] = f"https://www.whatsapp.com/otp/code/?otp_type={otp_type}&code={{{{1}}}}"
		button["url_type"] = "Dynamic"
		button["example_url"] = f"https://www.whatsapp.com/otp/code/?otp_type={otp_type}&code=123456"
	elif meta_type == "URL":
		button["website_url"] = meta_button.get("url")
		button["url_type"] = "Dynamic" if "{{" in button["website_url"] else "Static"
		if meta_button.get("example"):
			button["example_url"] = ",".join(meta_button["example"])
	elif meta_type == "PHONE_NUMBER":
		button["phone_number"] = meta_button.get("phone_number")
	elif meta_type == "FLOW":
		button["flow"] = meta_button.get("flow")

	return button


def upsert_without_hooks(doc, child_doctype, child_field):
	"""
	Insert or update a document and its child rows without running its hooks.

	Hooks are skipped on purpose: saving normally would push the template
	straight back to Meta.

	Parameters:
		doc (Document, required): Parent document.
		child_doctype (str, required): Child table DocType, e.g. "WhatsApp Button".
		child_field (str, required): Table fieldname, e.g. "buttons".

	Returns:
		None
	"""
	if frappe.db.exists(doc.doctype, doc.name):
		doc.db_update()
		frappe.db.delete(child_doctype, {"parent": doc.name, "parenttype": doc.doctype})
	else:
		doc.db_insert()

	for row in doc.get(child_field):
		row.parent = doc.name
		row.parenttype = doc.doctype
		row.parentfield = child_field
		row.db_insert()


def throw_fetch_error(error):
	"""
	Show Meta's error for a failed fetch, falling back to the Python error.

	Parameters:
		error (Exception, required): The exception from the request.

	Returns:
		None (always raises).
	"""
	if not hasattr(frappe.flags.integration_request, "json"):
		frappe.throw(f"An unexpected server error occurred: {error}")

	meta_error = get_meta_error()
	if not meta_error:
		frappe.throw(f"An unexpected error occurred while fetching templates: {error}")

	frappe.throw(msg=meta_error.get("error_user_msg", meta_error.get("message")), title=meta_error.get("error_user_title", "Error"))
