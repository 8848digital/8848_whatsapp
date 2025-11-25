// Copyright (c) 2025, 8848 and contributors
// For license information, please see license.txt

frappe.ui.form.on("WhatsApp Report Sender", {
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
