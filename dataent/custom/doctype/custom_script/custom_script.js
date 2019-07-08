// Copyright (c) 2016, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.ui.form.on('Custom Script', {
	refresh: function(frm) {
		if (frm.doc.dt && frm.doc.script) {
			frm.add_web_link("/desk#List/" + encodeURIComponent(frm.doc.dt) + "/List", "Test Script");
		}
	}
});
