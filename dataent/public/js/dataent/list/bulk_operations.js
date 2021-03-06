export default class BulkOperations {
	constructor({ doctype }) {
		if (!doctype) dataent.throw(__('Doctype required'));
		this.doctype = doctype;
	}

	print(docs) {
		const print_settings = dataent.model.get_doc(':Print Settings', 'Print Settings');
		const allow_print_for_draft = cint(print_settings.allow_print_for_draft);
		const is_submittable = dataent.model.is_submittable(this.doctype);
		const allow_print_for_cancelled = cint(print_settings.allow_print_for_cancelled);

		const valid_docs = docs.filter(doc => {
			return !is_submittable || doc.docstatus === 1 ||
				(allow_print_for_cancelled && doc.docstatus == 2) ||
				(allow_print_for_draft && doc.docstatus == 0) ||
				dataent.user.has_role('Administrator');
		}).map(doc => doc.name);

		const invalid_docs = docs.filter(doc => !valid_docs.includes(doc.name));

		if (invalid_docs.length > 0) {
			dataent.msgprint(__('You selected Draft or Cancelled documents'));
			return;
		}

		if (valid_docs.length > 0) {
			const dialog = new dataent.ui.Dialog({
				title: __('Print Documents'),
				fields: [{
					'fieldtype': 'Check',
					'label': __('With Letterhead'),
					'fieldname': 'with_letterhead'
				},
				{
					'fieldtype': 'Select',
					'label': __('Print Format'),
					'fieldname': 'print_sel',
					options: dataent.meta.get_print_formats(this.doctype)
				}]
			});

			dialog.set_primary_action(__('Print'), args => {
				if (!args) return;
				const default_print_format = dataent.get_meta(this.doctype).default_print_format;
				const with_letterhead = args.with_letterhead ? 1 : 0;
				const print_format = args.print_sel ? args.print_sel : default_print_format;
				const json_string = JSON.stringify(valid_docs);

				const w = window.open('/api/method/dataent.utils.print_format.download_multi_pdf?' +
					'doctype=' + encodeURIComponent(this.doctype) +
					'&name=' + encodeURIComponent(json_string) +
					'&format=' + encodeURIComponent(print_format) +
					'&no_letterhead=' + (with_letterhead ? '0' : '1'));
				if (!w) {
					dataent.msgprint(__('Please enable pop-ups'));
					return;
				}
			});

			dialog.show();
		} else {
			dataent.msgprint(__('Select atleast 1 record for printing'));
		}
	}

	delete(docnames, done = null) {
		dataent
			.call({
				method: 'dataent.desk.reportview.delete_items',
				freeze: true,
				args: {
					items: docnames,
					doctype: this.doctype
				}
			})
			.then((r) => {
				let failed = r.message;
				if (!failed) failed = [];

				if (failed.length && !r._server_messages) {
					dataent.throw(__('Cannot delete {0}', [failed.map(f => f.bold()).join(', ')]));
				}
				if (failed.length < docnames.length) {
					dataent.utils.play_sound('delete');
					if (done) done();
				}
			});
	}

	assign(docnames, done) {
		if (docnames.length > 0) {
			const assign_to = new dataent.ui.form.AssignToDialog({
				obj: this,
				method: 'dataent.desk.form.assign_to.add_multiple',
				doctype: this.doctype,
				docname: docnames,
				bulk_assign: true,
				re_assign: true,
				callback: done
			});
			assign_to.dialog.clear();
			assign_to.dialog.show();
		} else {
			dataent.msgprint(__('Select records for assignment'));
		}
	}

	submit_or_cancel(docnames, action='submit', done=null) {
		action = action.toLowerCase();
		dataent
			.call({
				method: 'dataent.desk.doctype.bulk_update.bulk_update.submit_cancel_or_update_docs',
				args: {
					doctype: this.doctype,
					action: action,
					docnames: docnames
				},
			})
			.then((r) => {
				let failed = r.message;
				if (!failed) failed = [];

				if (failed.length && !r._server_messages) {
					dataent.throw(__('Cannot {0} {1}', [action, failed.map(f => f.bold()).join(', ')]));
				}
				if (failed.length < docnames.length) {
					dataent.utils.play_sound(action);
					if (done) done();
				}
			});
	}

	edit(docnames, field_mappings, done) {
		let field_options = Object.keys(field_mappings).sort();
		const status_regex = /status/i;

		const default_field = field_options.find(value => status_regex.test(value));

		const dialog = new dataent.ui.Dialog({
			title: __('Edit'),
			fields: [
				{
					'fieldtype': 'Select',
					'options': field_options,
					'default': default_field,
					'label': __('Field'),
					'fieldname': 'field',
					'reqd': 1,
					'onchange': () => {
						set_value_field(dialog);
					}
				},
				{
					'fieldtype': 'Data',
					'label': __('Value'),
					'fieldname': 'value',
					'reqd': 1
				}
			],
			primary_action: ({ value }) => {
				const fieldname = field_mappings[dialog.get_value('field')].fieldname;
				dialog.disable_primary_action();
				dataent.call({
					method: 'dataent.desk.doctype.bulk_update.bulk_update.submit_cancel_or_update_docs',
					args: {
						doctype: this.doctype,
						freeze: true,
						docnames: docnames,
						action: 'update',
						data: {
							[fieldname]: value
						}
					}
				}).then(r => {
					let failed = r.message || [];

					if (failed.length && !r._server_messages) {
						dialog.enable_primary_action();
						dataent.throw(__('Cannot update {0}', [failed.map(f => f.bold ? f.bold() : f).join(', ')]));
					}
					done();
					dialog.hide();
				});
			},
			primary_action_label: __('Update')
		});

		if (default_field) set_value_field(dialog); // to set `Value` df based on default `Field`

		function set_value_field(dialogObj) {
			const new_df = Object.assign({},
				field_mappings[dialogObj.get_value('field')]);
			/* if the field label has status in it and
			if it has select fieldtype with no default value then
			set a default value from the available option. */
			if(new_df.label.match(status_regex) &&
				new_df.fieldtype === 'Select' && !new_df.default) {
				let options = [];
				if(typeof new_df.options==="string") {
					options = new_df.options.split("\n");
				}
				//set second option as default if first option is an empty string
				new_df.default = options[0] || options[1];
			}
			new_df.label = __('Value');
			new_df.reqd = 1;
			delete new_df.depends_on;
			dialogObj.replace_field('value', new_df);
		}

		dialog.refresh();
		dialog.show();
	}
}
