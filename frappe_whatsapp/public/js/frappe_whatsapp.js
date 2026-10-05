// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.
// Copyright (c) 2022, Shridhar Patil and contributors
// For license information, please see license.txt

frappe.provide("frappe_whatsapp");

/**
 * Call a frappe_whatsapp API method.
 *
 * Our endpoints reply in the standard envelope ({status, message, data, errors}),
 * so the callback gets `data`, and a failed call shows `message` (Frappe's own
 * error dialog doesn't understand the envelope and would stay silent).
 *
 * @param {Object} opts - Same options as frappe.call; `callback` receives the envelope's data.
 * @returns {Promise} The frappe.call promise.
 */
frappe_whatsapp.call = function (opts) {
	const { callback, error, ...call_opts } = opts;

	return frappe.call({
		...call_opts,
		callback(r) {
			if (callback) callback(r.data);
		},
		error(response) {
			show_api_error(response);
			if (error) error(response);
		},
	});
};

$(document).on("app_ready", function () {
	frappe.router.on("change", () => {
		const route = frappe.get_route();
		if (route && route[0] == "Form") {
			frappe.ui.form.on(route[1], {
				/**
				 * Add the Send To Whatsapp menu item to the form.
				 *
				 * @param {Object} frm - The open form.
				 * @returns {void}
				 */
				refresh(frm) {
					frm.page.add_menu_item(__("Send To Whatsapp"), () => show_send_dialog(frm));
				},
			});
		}
	});
});

/**
 * Show the "Send To Whatsapp" dialog for the open document.
 *
 * @param {Object} frm - The current form.
 * @returns {void}
 */
function show_send_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Send a WhatsApp Message"),
		fields: [
			{
				label: __("Select Template"),
				fieldname: "template",
				fieldtype: "Link",
				options: "WhatsApp Templates",
				reqd: 1,
				get_query: () => ({ filters: { for_doctype: frm.doc.doctype } }),
			},
			{
				label: __("Send to"),
				fieldname: "contact",
				fieldtype: "Link",
				options: "Contact",
				reqd: 1,
				change: () => fill_mobile_no(dialog),
			},
			{ label: __("Mobile no"), fieldname: "mobile_no", fieldtype: "Data" },
		],
		primary_action_label: __("Send"),
		primary_action(values) {
			send_template(frm, dialog, values);
		},
		no_submit_on_enter: true,
	});

	dialog.show();
}

/**
 * Copy the picked contact's mobile number into the dialog.
 *
 * @param {Object} dialog - The send dialog.
 * @returns {void}
 */
function fill_mobile_no(dialog) {
	const contact = dialog.get_value("contact");
	if (!contact) {
		dialog.set_value("mobile_no", "");
		return;
	}

	frappe.db.get_value("Contact", contact, "mobile_no").then((r) => {
		const mobile_no = r.message && r.message.mobile_no;
		dialog.set_value("mobile_no", mobile_no || "");
		if (!mobile_no) {
			frappe.msgprint(__("Mobile number not found for the selected contact."));
		}
	});
}

/**
 * Send the template, then log a comment on the document.
 *
 * @param {Object} frm - The current form.
 * @param {Object} dialog - The send dialog, closed on success.
 * @param {Object} values - Dialog values: template and mobile_no.
 * @returns {void}
 */
function send_template(frm, dialog, values) {
	frappe_whatsapp.call({
		method: "frappe_whatsapp.frappe_whatsapp.api.v1.message.send_template",
		args: {
			to: values.mobile_no,
			template: values.template,
			reference_doctype: frm.doc.doctype,
			reference_name: frm.doc.name,
		},
		freeze: true,
		callback: () => {
			frappe.msgprint(__("Successfully Sent to: {0}", [values.mobile_no]));
			dialog.hide();
			add_sent_comment(frm, values);
		},
	});
}

/**
 * Leave a comment on the document saying which template went to which number.
 *
 * @param {Object} frm - The current form.
 * @param {Object} values - Dialog values: template and mobile_no.
 * @returns {void}
 */
function add_sent_comment(frm, values) {
	frappe.call({
		method: "frappe.desk.form.utils.add_comment",
		args: {
			reference_doctype: frm.doc.doctype,
			reference_name: frm.doc.name,
			content: `To : ${values.mobile_no}\n\nWhatsapp Template: ${values.template}`,
			comment_email: frappe.session.user,
			comment_by: frappe.session.user_fullname,
		},
	});
}

/**
 * Show the error message from a failed frappe_whatsapp API call.
 *
 * @param {Object} response - The xhr, or the parsed body for some status codes.
 * @returns {void}
 */
function show_api_error(response) {
	const body = (response && response.responseJSON) || response;
	if (body && body.status === false && body.message) {
		frappe.msgprint({ title: __("Error"), message: body.message, indicator: "red" });
	}
}
