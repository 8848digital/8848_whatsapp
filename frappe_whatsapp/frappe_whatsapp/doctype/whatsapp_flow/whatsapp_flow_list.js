// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.
// Copyright (c) 2025, Shridhar Patil and contributors
// For license information, please see license.txt

frappe.listview_settings["WhatsApp Flow"] = {
	/**
	 * Add the Sync from Meta button to the list.
	 *
	 * @param {Object} listview - The WhatsApp Flow list view.
	 * @returns {void}
	 */
	onload(listview) {
		listview.page.add_inner_button(__("Sync from Meta"), () => {
			frappe.prompt(
				[
					{
						fieldname: "whatsapp_account",
						fieldtype: "Link",
						label: __("WhatsApp Account"),
						options: "WhatsApp Account",
						reqd: 1,
					},
				],
				(values) => sync_all_flows(listview, values.whatsapp_account),
				__("Sync Flows from Meta"),
				__("Sync All")
			);
		});
	},
};

/**
 * Import new flows and refresh existing ones from Meta, then show the counts.
 *
 * @param {object} listview - The WhatsApp Flow list view.
 * @param {string} whatsapp_account - WhatsApp Account name.
 * @returns {void}
 */
function sync_all_flows(listview, whatsapp_account) {
	frappe_whatsapp.call({
		method: "frappe_whatsapp.frappe_whatsapp.api.v1.flow.sync_all_flows",
		args: { whatsapp_account },
		freeze: true,
		freeze_message: __("Syncing all flows from Meta..."),
		callback(counts) {
			if (!counts) return;
			frappe.msgprint({
				title: __("Sync Complete"),
				message: __("Imported: {0}<br>Updated: {1}<br>Skipped: {2}", [
					counts.imported,
					counts.updated,
					counts.skipped,
				]),
				indicator: "green",
			});
			listview.refresh();
		},
	});
}
