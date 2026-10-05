// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.
// Copyright (c) 2025, Shridhar Patil and contributors
// For license information, please see license.txt

const FLOW_API = "frappe_whatsapp.frappe_whatsapp.api.v1.flow";
const STATUS_COLORS = { Published: "green", Deprecated: "gray", Blocked: "red" };

frappe.ui.form.on("WhatsApp Flow", {
	/**
	 * Add the import and Meta action buttons, and show the flow status.
	 *
	 * @param {Object} frm - The WhatsApp Flow form.
	 * @returns {void}
	 */
	refresh(frm) {
		if (frm.is_new() || !frm.doc.flow_id) {
			frm.add_custom_button(__("Import from Meta"), () => show_import_dialog(frm), __("Actions"));
		}

		if (!frm.is_new()) add_action_buttons(frm);

		if (frm.doc.status) {
			frm.page.set_indicator(frm.doc.status, STATUS_COLORS[frm.doc.status] || "orange");
		}
	},
});

/**
 * Add the Meta action buttons that make sense for the flow's current state.
 *
 * @param {object} frm - The WhatsApp Flow form.
 * @returns {void}
 */
function add_action_buttons(frm) {
	const add = (label, handler) => frm.add_custom_button(label, handler, __("Actions"));

	if (!frm.doc.flow_id) {
		add(__("Create on WhatsApp"), () => run_flow_action(frm, "create_on_whatsapp", __("Creating flow on WhatsApp...")));
		return;
	}

	add(__("Sync from Meta"), () => run_flow_action(frm, "sync_from_whatsapp", __("Syncing flow from Meta...")));

	if (frm.doc.status === "Draft") {
		add(__("Upload Flow JSON"), () => run_flow_action(frm, "upload_flow_json", __("Uploading flow JSON...")));
		add(__("Publish"), () =>
			frappe.confirm(__("Are you sure you want to publish this flow? Published flows cannot be edited."), () =>
				run_flow_action(frm, "publish_flow", __("Publishing flow..."))
			)
		);
	}

	if (frm.doc.status === "Published") {
		add(__("Deprecate"), () =>
			frappe.confirm(__("Are you sure you want to deprecate this flow?"), () =>
				run_flow_action(frm, "deprecate_flow", __("Deprecating flow..."))
			)
		);
	}

	add(__("Send Test"), () => show_send_test_dialog(frm));
	add(__("Check Status"), () => run_flow_action(frm, "get_flow_status", __("Checking flow status...")));
	add(__("Get Preview URL"), () =>
		run_flow_action(frm, "get_flow_preview", __("Getting preview URL..."), {}, (preview_url) => {
			if (!preview_url) return;
			frappe.msgprint({
				title: __("Preview URL"),
				message: `<a href="${encodeURI(preview_url)}" target="_blank">${frappe.utils.escape_html(preview_url)}</a>`,
				indicator: "green",
			});
		})
	);
	add(__("Delete from WhatsApp"), () =>
		frappe.confirm(__("Are you sure you want to delete this flow from WhatsApp? This cannot be undone."), () =>
			run_flow_action(frm, "delete_from_whatsapp", __("Deleting flow..."))
		)
	);
}

/**
 * Call one of the flow endpoints for this flow, then reload the form.
 *
 * @param {object} frm - The WhatsApp Flow form.
 * @param {string} action - Endpoint name in api/v1/flow.py, e.g. "publish_flow".
 * @param {string} freeze_message - Text shown while waiting.
 * @param {object} [args] - Extra arguments for the endpoint.
 * @param {Function} [after] - Called with the endpoint's return value.
 * @returns {void}
 */
function run_flow_action(frm, action, freeze_message, args = {}, after = null) {
	frappe_whatsapp.call({
		method: `${FLOW_API}.${action}`,
		args: { flow: frm.doc.name, ...args },
		freeze: true,
		freeze_message,
		callback(result) {
			frm.reload_doc();
			if (after) after(result);
		},
	});
}

/**
 * Ask for a phone number and send the flow there as a test.
 *
 * @param {object} frm - The WhatsApp Flow form.
 * @returns {void}
 */
function show_send_test_dialog(frm) {
	frappe.prompt(
		[
			{
				fieldname: "phone_number",
				label: __("Phone Number"),
				fieldtype: "Data",
				reqd: 1,
				description: __(
					"Enter phone number with country code (e.g., 919876543210). Must be a registered test number for draft flows."
				),
			},
			{
				fieldname: "message",
				label: __("Message"),
				fieldtype: "Small Text",
				default: "Please fill out the form below",
			},
		],
		(values) =>
			run_flow_action(frm, "send_test", __("Sending test flow..."), {
				phone_number: values.phone_number,
				message: values.message,
			}),
		__("Send Test Flow"),
		__("Send")
	);
}

/**
 * Ask which WhatsApp Account to import a flow from.
 *
 * @param {object} frm - The WhatsApp Flow form.
 * @returns {void}
 */
function show_import_dialog(frm) {
	const account_dialog = new frappe.ui.Dialog({
		title: __("Import Flow from Meta"),
		fields: [
			{
				fieldname: "whatsapp_account",
				fieldtype: "Link",
				label: __("WhatsApp Account"),
				options: "WhatsApp Account",
				reqd: 1,
				default: frm.doc.whatsapp_account,
			},
		],
		primary_action_label: __("Fetch Flows"),
		primary_action(values) {
			account_dialog.hide();
			fetch_and_show_flows(values.whatsapp_account);
		},
	});
	account_dialog.show();
}

/**
 * Load the account's flows from Meta and let the user pick one.
 *
 * @param {string} whatsapp_account - WhatsApp Account name.
 * @returns {void}
 */
function fetch_and_show_flows(whatsapp_account) {
	frappe_whatsapp.call({
		method: `${FLOW_API}.get_whatsapp_flows`,
		args: { whatsapp_account },
		freeze: true,
		freeze_message: __("Fetching flows from Meta..."),
		callback(flows) {
			if (flows && flows.length > 0) {
				show_flows_selection_dialog(flows, whatsapp_account);
			} else {
				frappe.msgprint(__("No flows found on Meta Business Account"));
			}
		},
	});
}

/**
 * Show the account's flows in a table with an Import button for new ones.
 *
 * @param {Array<object>} flows - Flows from get_whatsapp_flows.
 * @param {string} whatsapp_account - WhatsApp Account name.
 * @returns {void}
 */
function show_flows_selection_dialog(flows, whatsapp_account) {
	const esc = frappe.utils.escape_html;
	const rows = flows
		.map((flow) => {
			const status_badge =
				flow.status === "PUBLISHED"
					? '<span class="badge badge-success">Published</span>'
					: '<span class="badge badge-warning">Draft</span>';
			const exists_badge = flow.exists_locally
				? `<span class="badge badge-info">Exists: ${esc(flow.local_name)}</span>`
				: '<span class="badge badge-secondary">Not imported</span>';
			const import_button = flow.exists_locally
				? '<button class="btn btn-xs btn-default" disabled>Already Imported</button>'
				: `<button class="btn btn-xs btn-primary import-flow-btn" data-flow-id="${esc(flow.id)}" data-flow-name="${esc(flow.name)}">Import</button>`;

			return `<tr>
				<td>${esc(flow.name)}</td>
				<td><code>${esc(flow.id)}</code></td>
				<td>${status_badge}</td>
				<td>${exists_badge}</td>
				<td>${import_button}</td>
			</tr>`;
		})
		.join("");

	const dialog = new frappe.ui.Dialog({
		title: __("Select Flow to Import"),
		size: "large",
		fields: [
			{
				fieldname: "flows_html",
				fieldtype: "HTML",
				options: `<table class="table table-bordered">
					<thead><tr>
						<th>${__("Flow Name")}</th><th>${__("Flow ID")}</th><th>${__("Status")}</th>
						<th>${__("Local Status")}</th><th>${__("Action")}</th>
					</tr></thead>
					<tbody>${rows}</tbody>
				</table>`,
			},
		],
	});
	dialog.show();

	dialog.$wrapper.find(".import-flow-btn").on("click", function () {
		dialog.hide();
		import_flow(whatsapp_account, $(this).data("flow-id"), $(this).data("flow-name"));
	});
}

/**
 * Import one flow from Meta and open it.
 *
 * @param {string} whatsapp_account - WhatsApp Account name.
 * @param {string} flow_id - Flow id on WhatsApp.
 * @param {string} flow_name - Name to give the local flow.
 * @returns {void}
 */
function import_flow(whatsapp_account, flow_id, flow_name) {
	frappe_whatsapp.call({
		method: `${FLOW_API}.import_flow_from_whatsapp`,
		args: { whatsapp_account, flow_id: String(flow_id), flow_name },
		freeze: true,
		freeze_message: __("Importing flow..."),
		callback(flow_name) {
			if (flow_name) frappe.set_route("Form", "WhatsApp Flow", flow_name);
		},
	});
}
