// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.
// Copyright (c) 2025, 8848 and contributors
// For license information, please see license.txt

frappe.ui.form.on("WhatsApp Report Sender", {
	/**
	 * Only offer print formats of the chosen document's DocType.
	 *
	 * @param {Object} frm - The WhatsApp Report Sender form.
	 * @returns {void}
	 */
	refresh(frm) {
        if (frm.doc.document_doctype){
            frm.set_query("print_format", function() {
                return {
                    filters: {
                        doc_type: frm.doc.document_doctype
                    }
                };
            });
        }
	}
});
