// Copyright (c) 2017, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.ui.form.on('User Permission', {
	setup: frm => {
		frm.set_query("allow", () => {
			return {
				"filters": {
					issingle: 0,
					istable: 0
				}
			};
		});

		frm.set_query('applicable_for', () => {
			return {
				'query': 'dataent.core.doctype.user_permission.user_permission.get_applicable_for_doctype_list',
				'doctype': frm.doc.allow
			};
		});

	},

	refresh: frm => {
		frm.add_custom_button(__('View Permitted Documents'),
			() => dataent.set_route('query-report', 'Permitted Documents For User',
				{ user: frm.doc.user }));
		frm.trigger('set_applicable_for_constraint');
	},

	allow: frm => {
		if(frm.doc.for_value) {
			frm.set_value('for_value', null);
		}
	},

	apply_to_all_doctypes: frm => {
		frm.trigger('set_applicable_for_constraint');
	},

	set_applicable_for_constraint: frm => {
		frm.toggle_reqd('applicable_for', !frm.doc.apply_to_all_doctypes);
		if (frm.doc.apply_to_all_doctypes) {
			frm.set_value('applicable_for', null);
		}
	}


});
