// Copyright (c) 2016, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.ui.form.on("Address", {
	refresh: function(frm) {
		if(frm.doc.__islocal) {
			const last_doc = dataent.contacts.get_last_doc(frm);
			if(dataent.dynamic_link && dataent.dynamic_link.doc
					&& dataent.dynamic_link.doc.name == last_doc.docname) {
				frm.set_value('links', '');
				frm.add_child('links', {
					link_doctype: dataent.dynamic_link.doctype,
					link_name: dataent.dynamic_link.doc[dataent.dynamic_link.fieldname]
				});
			}
		}
		frm.set_query('link_doctype', "links", function() {
			return {
				query: "dataent.contacts.address_and_contact.filter_dynamic_link_doctypes",
				filters: {
					fieldtype: "HTML",
					fieldname: "address_html",
				}
			}
		});
		frm.refresh_field("links");
	},
	validate: function(frm) {
		// clear linked customer / supplier / sales partner on saving...
		if(frm.doc.links) {
			frm.doc.links.forEach(function(d) {
				dataent.model.remove_from_locals(d.link_doctype, d.link_name);
			});
		}
	},
	after_save: function(frm) {
		dataent.run_serially([
			() => dataent.timeout(1),
			() => {
				const last_doc = dataent.contacts.get_last_doc(frm);
				if(dataent.dynamic_link && dataent.dynamic_link.doc
					&& dataent.dynamic_link.doc.name == last_doc.docname){
					dataent.set_route('Form', last_doc.doctype, last_doc.docname);
				}
			}
		]);
	}
});
