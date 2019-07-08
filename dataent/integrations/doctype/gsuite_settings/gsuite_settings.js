// Copyright (c) 2017, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.ui.form.on('GSuite Settings', {
	refresh: function(frm) {
		frm.clear_custom_buttons();
	},

	allow_gsuite_access: function(frm) {
		if (frm.doc.client_id && frm.doc.client_secret) {
			dataent.call({
				method: "dataent.integrations.doctype.gsuite_settings.gsuite_settings.gsuite_callback",
				callback: function(r) {
					if(!r.exc) {
						frm.save();
						window.open(r.message.url);
					}
				}
			});
		}
		else {
			dataent.msgprint(__("Please enter values for GSuite Access Key and GSuite Access Secret"))
		}
	},
	run_script_test: function(frm) {
		if (frm.doc.client_id && frm.doc.client_secret) {
			dataent.call({
				method: "dataent.integrations.doctype.gsuite_settings.gsuite_settings.run_script_test",
				callback: function(r) {
					if(!r.exc) {
						if (r.message == 'ping') {
							dataent.msgprint(__('GSuite test executed with success. GSuite integration is correctly configured'),__('GSuite script test'));
						}
					}
				}
			});
		}
		else {
			dataent.msgprint(__("Please enter values for GSuite Access Key and GSuite Access Secret"));
		}
	}
});
