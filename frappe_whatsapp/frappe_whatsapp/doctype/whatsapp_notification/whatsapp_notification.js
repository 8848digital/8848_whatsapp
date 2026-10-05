// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.
// Copyright (c) 2022, Shridhar Patil and contributors
// For license information, please see license.txt
frappe.notification = {
	/**
	 * Fill the field pickers (phone field, date field, value-changed and set-property fields)
	 * from the reference DocType's fields.
	 *
	 * @param {object} frm - The WhatsApp Notification form.
	 * @returns {void}
	 */
	setup_fieldname_select: function (frm) {
		// get the doctype to update fields
		if (!frm.doc.reference_doctype) {
			return;
		}

		frappe.model.with_doctype(frm.doc.reference_doctype, function () {
			let get_select_options = function (df, parent_field) {
				// Append parent_field name along with fieldname for child table fields
				let select_value = parent_field ? df.fieldname + "," + parent_field : df.fieldname;
				let path = parent_field ? parent_field + " > " + df.fieldname : df.fieldname;

				return {
					value: select_value,
					label: path + " (" + __(df.label, null, df.parent) + ")",
				};
			};

			let get_date_change_options = function () {
				let date_options = $.map(fields, function (d) {
					return d.fieldtype == "Date" || d.fieldtype == "Datetime"
						? get_select_options(d)
						: null;
				});
				// append creation and modified date to Date Change field
				return date_options.concat([
					{ value: "creation", label: `creation (${__("Created On")})` },
					{ value: "modified", label: `modified (${__("Last Modified Date")})` },
				]);
			};

			let fields = frappe.get_doc("DocType", frm.doc.reference_doctype).fields;
			let options = $.map(fields, function (d) {
				return frappe.model.no_value_type.includes(d.fieldtype)
					? null
					: get_select_options(d);
			});

			// set date changed options
			frm.set_df_property("date_changed", "options", get_date_change_options());

			// set value changed options
			frm.set_df_property("value_changed", "options", [""].concat(options));
			frm.set_df_property("set_property_after_alert", "options", [""].concat(options));
		});
	},
	/**
	 * Add the "Get Alerts for Today" button, which sends today's date-based notifications now.
	 *
	 * @param {object} frm - The WhatsApp Notification form.
	 * @returns {void}
	 */
	setup_alerts_button: function (frm) {
		frm.add_custom_button(__("Get Alerts for Today"), () => {
			frappe_whatsapp.call({
				method: "frappe_whatsapp.frappe_whatsapp.api.v1.notification.call_trigger_notifications",
				freeze: true,
				callback() {
					frappe.show_alert({ message: __("Today's alerts were sent"), indicator: "green" });
				},
			});
		});
	}
};


frappe.ui.form.on('WhatsApp Notification', {
	/**
	 * Load the template preview and set up the field picker and alerts button.
	 *
	 * @param {Object} frm - The WhatsApp Notification form.
	 * @returns {void}
	 */
	refresh: function(frm) {
		frm.trigger("load_template")
		frappe.notification.setup_fieldname_select(frm);
		frappe.notification.setup_alerts_button(frm);
	},
	/**
	 * Reload the template preview when the template changes.
	 *
	 * @param {Object} frm - The WhatsApp Notification form.
	 * @returns {void}
	 */
	template: function(frm){
		frm.trigger("load_template")
	},
	/**
	 * Show the template text, and the attachment options when its header is a document or image.
	 *
	 * @param {Object} frm - The WhatsApp Notification form.
	 * @returns {void}
	 */
	load_template: function(frm){
		frappe.db.get_value(
			"WhatsApp Templates",
			frm.doc.template,
			["template", "header_type"],
			(r) => {
				if (r && r.template) {
					frm.set_value('header_type', r.header_type)
					frm.refresh_field("header_type")
					if (['DOCUMENT', "IMAGE"].includes(r.header_type)){
						frm.toggle_display("custom_attachment", true);
						frm.toggle_display("attach_document_print", true);
						if (!frm.doc.custom_attachment){
							frm.set_value("attach_document_print", 1)
						}
					}else{
						frm.toggle_display("custom_attachment", false);
						frm.toggle_display("attach_document_print", false);
						frm.set_value("attach_document_print", 0)
						frm.set_value("custom_attachment", 0)
					}

					frm.refresh_field("custom_attachment")

					frm.set_value("code", r.template);
					frm.refresh_field("code")
				}
			}
		)
	},
	/**
	 * Require a file name for a custom attachment, and untick the document print.
	 *
	 * @param {Object} frm - The WhatsApp Notification form.
	 * @returns {void}
	 */
	custom_attachment: function(frm){
		if(frm.doc.custom_attachment == 1 &&  ['DOCUMENT', "IMAGE"].includes(frm.doc.header_type)){
			frm.set_df_property('file_name', 'reqd', frm.doc.custom_attachment)
		}else{
			frm.set_df_property('file_name', 'reqd', 0)
		}

		if(frm.doc.header_type){
			frm.set_value("attach_document_print", !frm.doc.custom_attachment)
		}
	},
	/**
	 * Attaching the document print and a custom file are either-or.
	 *
	 * @param {Object} frm - The WhatsApp Notification form.
	 * @returns {void}
	 */
	attach_document_print: function(frm){
		if(['DOCUMENT', "IMAGE"].includes(frm.doc.header_type)){
			frm.set_value("custom_attachment", !frm.doc.attach_document_print)
		}
	},
	/**
	 * Refresh the field picker for the new DocType.
	 *
	 * @param {Object} frm - The WhatsApp Notification form.
	 * @returns {void}
	 */
	reference_doctype: function (frm) {
		frappe.notification.setup_fieldname_select(frm);
	},
});
