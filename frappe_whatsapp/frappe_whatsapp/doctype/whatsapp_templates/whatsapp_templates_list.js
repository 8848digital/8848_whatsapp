// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.
// Copyright (c) 2022, Shridhar Patil and contributors
// For license information, please see license.txt

frappe.listview_settings["WhatsApp Templates"] = {
	/**
	 * Add the Sync from Meta button to the list.
	 *
	 * @param {Object} listview - The WhatsApp Templates list view.
	 * @returns {void}
	 */
	onload(listview) {
		listview.page.add_inner_button(__("Sync from Meta"), () => {
			frappe_whatsapp.call({
				method: "frappe_whatsapp.frappe_whatsapp.api.v1.template.fetch",
				freeze: true,
				freeze_message: __("Syncing templates from Meta..."),
				callback(message) {
					if (!message) return;
					frappe.msgprint({ title: __("Sync Complete"), message, indicator: "green" });
					listview.refresh();
				},
			});
		});
	},
};
