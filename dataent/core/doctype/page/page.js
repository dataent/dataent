// Copyright (c) 2016, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.ui.form.on('Page', {
	refresh: function(frm) {
		if(!dataent.boot.developer_mode && user != 'Administrator') {
			// make the document read-only
			frm.set_read_only();
		}
	}
});
