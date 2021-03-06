// Copyright (c) 2018, Dataent Technologies and contributors
// For license information, please see license.txt
dataent.provide("dataent.auto_repeat");

dataent.ui.form.on('Auto Repeat', {
	setup: function(frm) {
		frm.fields_dict['reference_doctype'].get_query = function() {
			return {
				query: "dataent.desk.doctype.auto_repeat.auto_repeat.auto_repeat_doctype_query"
			};
		};

		frm.fields_dict['reference_document'].get_query = function() {
			return {
				filters: {
					"docstatus": 1,
					"auto_repeat": ''
				}
			};
		};

		frm.fields_dict['print_format'].get_query = function() {
			return {
				filters: {
					"doc_type": frm.doc.reference_doctype
				}
			};
		};
	},

	refresh: function(frm) {

		if(frm.doc.docstatus == 1) {

			let label = __('View {0}', [__(frm.doc.reference_doctype)]);
			frm.add_custom_button(__(label),
				function() {
					dataent.route_options = {
						"auto_repeat": frm.doc.name,
					};
					dataent.set_route("List", frm.doc.reference_doctype);
				}
			);

			if(frm.doc.status != 'Stopped') {
				frm.add_custom_button(__("Stop"),
					function() {
						frm.events.stop_resume_auto_repeat(frm, "Stopped");
					}
				);
			}

			if(frm.doc.status == 'Stopped') {
				frm.add_custom_button(__("Restart"),
					function() {
						frm.events.stop_resume_auto_repeat(frm, "Resumed");
					}
				);
			}
		}

		frm.toggle_display('auto_repeat_schedule', !in_list(['Stopped', 'Cancelled'], frm.doc.status));
		if(frm.doc.start_date && !in_list(['Stopped', 'Cancelled'], frm.doc.status)){
			dataent.auto_repeat.render_schedule(frm);
		}

	},

	stop_resume_auto_repeat: function(frm, status) {
		dataent.call({
			method: "dataent.desk.doctype.auto_repeat.auto_repeat.stop_resume_auto_repeat",
			args: {
				auto_repeat: frm.doc.name,
				status: status
			},
			callback: function(r) {
				if(r.message) {
					frm.set_value("status", r.message);
					frm.reload_doc();
				}
			}
		});
	},

	template: function(frm) {
		if (frm.doc.template) {
			dataent.model.with_doc("Email Template", frm.doc.template, () => {
				let email_template = dataent.get_doc("Email Template", frm.doc.template);
				frm.set_value("subject", email_template.subject);
				frm.set_value("message", email_template.response);
				frm.refresh_field("subject");
				frm.refresh_field("message");
			});
		}
	},

	get_contacts: function(frm) {
		dataent.call({
			method: "dataent.desk.doctype.auto_repeat.auto_repeat.get_contacts",
			args: {
				reference_doctype: frm.doc.reference_doctype,
				reference_name: frm.doc.reference_document
			},
			callback: function(r) {
				if(r.message) {
					frm.set_value("recipients", r.message.join());
					frm.refresh_field("recipients");
				}
			}
		});
	},

	preview_message: function(frm) {
		if (frm.doc.message) {
			dataent.call({
				method: "dataent.desk.doctype.auto_repeat.auto_repeat.generate_message_preview",
				args: {
					reference_dt: frm.doc.reference_doctype,
					reference_doc: frm.doc.reference_document,
					subject: frm.doc.subject,
					message: frm.doc.message
				},
				callback: function(r) {
					if(r.message) {
						dataent.msgprint(r.message.message, r.message.subject)
					}
				}
			});
		} else {
			dataent.msgprint(__("Please setup a message first"), __("Message not setup"))
		}
	}
});

dataent.auto_repeat.render_schedule = function(frm) {
	dataent.call({
		method: "get_auto_repeat_schedule",
		doc: frm.doc
	}).done((r) => {
		var wrapper = $(frm.fields_dict["auto_repeat_schedule"].wrapper);
		wrapper.html(dataent.render_template ("auto_repeat_schedule", {"schedule_details" : r.message || []}  ));
		frm.refresh_fields();
	});
};