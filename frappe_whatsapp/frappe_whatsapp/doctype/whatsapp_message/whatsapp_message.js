// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.
// Copyright (c) 2022, Shridhar Patil and contributors
// For license information, please see license.txt

frappe.ui.form.on("WhatsApp Message", {
	/**
	 * Send the read receipt for an unread incoming message when the account does it automatically.
	 *
	 * @param {Object} frm - The WhatsApp Message form.
	 * @returns {void}
	 */
	onload(frm) {
		if (frm.doc.type !== "Incoming" || frm.doc.status === "marked as read" || !frm.doc.message_id) return;

		get_auto_read_receipt(frm).then((auto_read) => {
			if (auto_read) send_read_receipt(frm);
		});
	},

	/**
	 * Add the Reply and Mark as read buttons.
	 *
	 * @param {Object} frm - The WhatsApp Message form.
	 * @returns {void}
	 */
	refresh(frm) {
		if (frm.doc.type == "Incoming") {
			frm.add_custom_button(__("Reply"), () => frappe.new_doc("WhatsApp Message", { to: frm.doc.from }));
		}

		add_mark_as_read(frm);
	},
});

/**
 * Add a "Mark as read" button when the account doesn't send read receipts on its own.
 *
 * @param {object} frm - The WhatsApp Message form.
 * @returns {void}
 */
function add_mark_as_read(frm) {
	if (frm.doc.type === "Outgoing" || frm.doc.status == "marked as read" || !frm.doc.message_id) return;

	get_auto_read_receipt(frm).then((auto_read) => {
		if (auto_read) return;
		frm.add_custom_button(__("Mark as read"), () => send_read_receipt(frm));
	});
}

/**
 * Whether the message's WhatsApp Account sends read receipts automatically.
 *
 * @param {object} frm - The WhatsApp Message form.
 * @returns {Promise<boolean>} Resolves to the account's "Allow Auto Read Receipt" setting.
 */
function get_auto_read_receipt(frm) {
	return frappe.db
		.get_value("WhatsApp Account", frm.doc.whatsapp_account, "allow_auto_read_receipt")
		.then((r) => Boolean(r.message && r.message.allow_auto_read_receipt));
}

/**
 * Tell WhatsApp the message was read, then reload the form to show the new status.
 *
 * @param {object} frm - The WhatsApp Message form.
 * @returns {void}
 */
function send_read_receipt(frm) {
	frappe_whatsapp.call({
		method: "frappe_whatsapp.frappe_whatsapp.api.v1.message.send_read_receipt",
		args: { message: frm.doc.name },
		callback(marked) {
			if (marked) {
				frappe.msgprint(__("Marked as read"));
				frm.reload_doc();
			}
		},
	});
}
