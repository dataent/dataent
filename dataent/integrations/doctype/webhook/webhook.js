// Copyright (c) 2017, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.webhook = {
	set_fieldname_select: function(frm) {
		var doc = frm.doc;
		if (doc.webhook_doctype) {
			dataent.model.with_doctype(doc.webhook_doctype, function() {
				var fields = $.map(dataent.get_doc("DocType", frm.doc.webhook_doctype).fields, function(d) {
					if (dataent.model.no_value_type.indexOf(d.fieldtype) === -1 ||
						d.fieldtype === 'Table') {
						return { label: d.label + ' (' + d.fieldtype + ')', value: d.fieldname };
					}
					else if (d.fieldtype === 'Currency' || d.fieldtype === 'Float') {
						return { label: d.label, value: d.fieldname };
					}
					else {
						return null;
					}
				});
				fields.unshift({"label":"Name (Doc Name)","value":"name"});
				dataent.meta.get_docfield("Webhook Data", "fieldname", frm.doc.name).options = [""].concat(fields);
			});
		}
	}
};

dataent.ui.form.on('Webhook', {
	refresh: function(frm) {
		dataent.webhook.set_fieldname_select(frm);
	},
	webhook_doctype: function(frm) {
		dataent.webhook.set_fieldname_select(frm);
	}
});

dataent.ui.form.on("Webhook Data", {
	fieldname: function(frm, doctype, name) {
		var doc = dataent.get_doc(doctype, name);
		var df = $.map(dataent.get_doc("DocType", frm.doc.webhook_doctype).fields, function(d) {
			return doc.fieldname == d.fieldname ? d : null;
		})[0];
		doc.key = df != undefined ? df.fieldname : "name";
		frm.refresh_field("webhook_data");
	}
});
