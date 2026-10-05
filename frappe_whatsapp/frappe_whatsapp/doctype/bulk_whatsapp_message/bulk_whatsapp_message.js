// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.
// Copyright (c) 2022, Shridhar Patil and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk WhatsApp Message', {
    /**
     * Add the Check Progress and Retry Failed Messages buttons once the batch is sent.
     *
     * @param {Object} frm - The Bulk WhatsApp Message form.
     * @returns {void}
     */
    refresh: function(frm) {
        // Add progress bar
        if(frm.doc.docstatus === 1 && frm.doc.status != 'Draft') {
            frm.add_custom_button(__('Check Progress'), function() {
                frappe_whatsapp.call({
                    method: 'frappe_whatsapp.frappe_whatsapp.api.v1.bulk_messaging.get_progress',
                    args: {
                        name: frm.doc.name
                    },
                    callback: function(progress) {
                        if(progress) {
                            let html = `
                                <div class="progress" style="height: 20px;">
                                    <div class="progress-bar bg-success" role="progressbar" 
                                        style="width: ${progress.percent}%;" 
                                        aria-valuenow="${progress.percent}" 
                                        aria-valuemin="0" 
                                        aria-valuemax="100">
                                        ${Math.round(progress.percent)}%
                                    </div>
                                </div>
                                <div class="mt-2">
                                    <span class="badge badge-success">Sent: ${progress.sent}</span>
                                    <span class="badge badge-danger ml-2">Failed: ${progress.failed}</span>
                                    <span class="badge badge-warning ml-2">Queued: ${progress.queued}</span>
                                    <span class="badge badge-info ml-2">Total: ${progress.total}</span>
                                </div>
                            `;
                            
                            frappe.msgprint({
                                title: __('Message Progress'),
                                indicator: 'blue',
                                message: html
                            });
                        }
                    }
                });
            });
            
            // Add retry button
            frm.add_custom_button(__('Retry Failed Messages'), function() {
                frappe_whatsapp.call({
                    method: 'frappe_whatsapp.frappe_whatsapp.api.v1.bulk_messaging.retry_failed',
                    args: {
                        name: frm.doc.name
                    },
                    callback: function(retried) {
                        if(retried) {
                            frm.reload_doc();
                        }
                    }
                });
            }).addClass('btn-danger');
        }
    },
    /**
     * Stop the save when recipients, the template or the message text are missing.
     *
     * @param {Object} frm - The Bulk WhatsApp Message form.
     * @returns {boolean} True when the batch can be saved.
     */
    validate: function(frm) {
        if(frm.doc.recipient_type == 'Individual' && (!frm.doc.recipients || frm.doc.recipients.length === 0)) {
            frappe.throw(__('Please add at least one recipient'));
            return false;
        }
        
        if(frm.doc.recipient_type == 'Recipient List' && !frm.doc.recipient_list) {
            frappe.throw(__('Please select a recipient list'));
            return false;
        }
        
        if(frm.doc.use_template && !frm.doc.template) {
            frappe.throw(__('Please select a template'));
            return false;
        }
        
        if(!frm.doc.use_template && !frm.doc.message_content) {
            frappe.throw(__('Please enter message content'));
            return false;
        }
        
        return true;
    }
});
