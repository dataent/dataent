// Copyright (c) 2018, DOKOS and contributors
// For license information, please see license.txt

dataent.ui.form.on('GCalendar Account', {
	allow_google_access: function(frm) {
		dataent.call({
			method: "dataent.integrations.doctype.gcalendar_settings.gcalendar_settings.google_callback",
			args: {
				'account': frm.doc.name
			},
			callback: function(r) {
				if(!r.exc) {
					frm.save();
					window.open(r.message.url);
				}
			}
		});
	}
});
