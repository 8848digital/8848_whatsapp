// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.
// Copyright (c) 2025, Shridhar Patil and contributors
// For license information, please see license.txt

frappe.ui.form.on("WhatsApp Account", {
	/**
	 * Add the Subscribe App to Webhooks button on saved accounts.
	 *
	 * @param {Object} frm - The WhatsApp Account form.
	 * @returns {void}
	 */
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Subscribe App to Webhooks"), () => {
				frappe.confirm(
					__("Subscribe this app to webhooks for WhatsApp Business Account {0}?", [
						frm.doc.business_id || frm.doc.account_name,
					]),
					() => {
						frappe_whatsapp.call({
							method: "frappe_whatsapp.frappe_whatsapp.api.v1.account.subscribe_app",
							args: { account: frm.doc.name },
							freeze: true,
							freeze_message: __("Subscribing app to webhooks..."),
							callback: () => {
								frappe.show_alert({
									message: __("App subscribed to webhooks"),
									indicator: "green",
								});
							},
						});
					}
				);
			});
		}
	},
});
