// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.provide("dataent.ui.form");

dataent.ui.form.save = function (frm, action, callback, btn) {
	$(btn).prop("disabled", true);

	// specified here because there are keyboard shortcuts to save
	var working_label = {
		"Save": __("Saving"),
		"Submit": __("Submitting"),
		"Update": __("Updating"),
		"Amend": __("Amending"),
		"Cancel": __("Cancelling")
	}[toTitle(action)];

	var freeze_message = working_label ? __(working_label) : "";

	var save = function () {
		remove_empty_rows();

		$(frm.wrapper).addClass('validated-form');
		if (check_mandatory()) {
			_call({
				method: "dataent.desk.form.save.savedocs",
				args: { doc: frm.doc, action: action },
				callback: function (r) {
					$(document).trigger("save", [frm.doc]);
					callback(r);
				},
				error: function (r) {
					callback(r);
				},
				btn: btn,
				freeze_message: freeze_message
			});
		} else {
			$(btn).prop("disabled", false);
		}
	};

	var remove_empty_rows = function() {
		/**
		This function removes empty rows. Note that in this function, a row is considered
		empty if the fields with `in_list_view: 1` are undefined or falsy because that's
		what users also consider to be an empty row
		 */
		const docs = dataent.model.get_all_docs(frm.doc);

		// we should only worry about table data
		const tables = docs.filter(function(d){
			return dataent.model.is_table(d.doctype);
		});

		tables.map(
			function(doc){
				const cells = dataent.meta.docfield_list[doc.doctype] || [];

				const in_list_view_cells = cells.filter(function(df) {
					return cint(df.in_list_view) === 1;
				});

				var is_empty_row = function(cells) {
					for (var i=0; i < cells.length; i++){
						if(locals[doc.doctype][doc.name][cells[i].fieldname]){
							return false;
						}
					}
					return true;
				}

				if (is_empty_row(in_list_view_cells)) {
					dataent.model.clear_doc(doc.doctype, doc.name);
				}
			}
		);
	};

	var cancel = function () {
		var args = {
			doctype: frm.doc.doctype,
			name: frm.doc.name
		};

		// update workflow state value if workflow exists
		var workflow_state_fieldname = dataent.workflow.get_state_fieldname(frm.doctype);
		if (workflow_state_fieldname) {
			$.extend(args, {
				workflow_state_fieldname: workflow_state_fieldname,
				workflow_state: frm.doc[workflow_state_fieldname]

			});
		}

		_call({
			method: "dataent.desk.form.save.cancel",
			args: args,
			callback: function (r) {
				$(document).trigger("save", [frm.doc]);
				callback(r);
			},
			btn: btn,
			freeze_message: freeze_message
		});
	};

	var check_mandatory = function () {
		var me = this;
		var has_errors = false;
		frm.scroll_set = false;

		if (frm.doc.docstatus == 2) return true; // don't check for cancel

		$.each(dataent.model.get_all_docs(frm.doc), function (i, doc) {
			var error_fields = [];
			var folded = false;

			$.each(dataent.meta.docfield_list[doc.doctype] || [], function (i, docfield) {
				if (docfield.fieldname) {
					var df = dataent.meta.get_docfield(doc.doctype,
						docfield.fieldname, frm.doc.name);

					if (df.fieldtype === "Fold") {
						folded = frm.layout.folded;
					}

					if (df.reqd && !dataent.model.has_value(doc.doctype, doc.name, df.fieldname)) {
						has_errors = true;
						error_fields[error_fields.length] = __(df.label);
						// scroll to field
						if (!frm.scroll_set) {
							scroll_to(doc.parentfield || df.fieldname);
						}

						if (folded) {
							frm.layout.unfold();
							folded = false;
						}
					}

				}
			});

			if (error_fields.length) {
				if (doc.parenttype) {
					var message = __('Mandatory fields required in table {0}, Row {1}',
						[__(dataent.meta.docfield_map[doc.parenttype][doc.parentfield].label).bold(), doc.idx]);
				} else {
					var message = __('Mandatory fields required in {0}', [__(doc.doctype)]);

				}
				message = message + '<br><br><ul><li>' + error_fields.join('</li><li>') + "</ul>";
				dataent.msgprint({
					message: message,
					indicator: 'red',
					title: __('Missing Fields')
				});
			}
		});

		return !has_errors;
	};

	var scroll_to = function (fieldname) {
		var f = cur_frm.fields_dict[fieldname];
		if (f) {
			$(document).scrollTop($(f.wrapper).offset().top - 60);
		}
		frm.scroll_set = true;
	};

	var _call = function (opts) {
		// opts = {
		// 	method: "some server method",
		// 	args: {args to be passed},
		// 	callback: callback,
		// 	btn: btn
		// }

		if (dataent.ui.form.is_saving) {
			// this is likely to happen if the user presses the shortcut cmd+s for a longer duration or uses double click
			// no need to show this to user, as they can see "Saving" in freeze message
			console.log("Already saving. Please wait a few moments.")
			throw "saving";
		}

		// ensure we remove new docs routes ONLY
		if ( frm.is_new() ) {
			dataent.ui.form.remove_old_form_route();
		}
		dataent.ui.form.is_saving = true;

		return dataent.call({
			freeze: true,
			// freeze_message: opts.freeze_message,
			method: opts.method,
			args: opts.args,
			btn: opts.btn,
			callback: function (r) {
				opts.callback && opts.callback(r);
			},
			error: opts.error,
			always: function (r) {
				$(btn).prop("disabled", false);
				dataent.ui.form.is_saving = false;
				if (r) {
					var doc = r.docs && r.docs[0];
					if (doc) {
						dataent.ui.form.update_calling_link(doc);
					}
				}
			}
		})
	};

	if (action === "cancel") {
		cancel();
	} else {
		save();
	}
}

dataent.ui.form.remove_old_form_route = () => {
	let current_route = dataent.get_route().join("/");
	dataent.route_history = dataent.route_history
		.filter((route) => route.join("/") !== current_route);
}

dataent.ui.form.update_calling_link = (newdoc) => {
	if (dataent._from_link && newdoc.doctype === dataent._from_link.df.options) {
		var doc = dataent.get_doc(dataent._from_link.doctype, dataent._from_link.docname);
		// set value
		if (doc && doc.parentfield) {
			//update values for child table
			$.each(dataent._from_link.frm.fields_dict[doc.parentfield].grid.grid_rows, function (index, field) {
				if (field.doc && field.doc.name === dataent._from_link.docname) {
					dataent._from_link.set_value(newdoc.name);
				}
			});
		} else {
			dataent._from_link.set_value(newdoc.name);
		}

		// refresh field
		dataent._from_link.refresh();

		// if from form, switch
		if (dataent._from_link.frm) {
			dataent.set_route("Form",
				dataent._from_link.frm.doctype, dataent._from_link.frm.docname)
				.then(() => {
					dataent.utils.scroll_to(dataent._from_link_scrollY);
				});
		}

		dataent._from_link = null;
	}
}

