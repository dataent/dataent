// Copyright (c) 2016, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.ui.form.on('Bulk Update', {
	refresh: function(frm) {
		frm.page.set_primary_action(__('Update'), function() {
			if (!frm.doc.update_value) {
				dataent.throw(__('Field "value" is mandatory. Please specify value to be updated'));
			} else {
				dataent.call({
					method: 'dataent.desk.doctype.bulk_update.bulk_update.update',
					args: {
						doctype: frm.doc.document_type,
						field: frm.doc.field,
						value: frm.doc.update_value,
						condition: frm.doc.condition,
						limit: frm.doc.limit
					},
				}).then(r => {
					let failed = r.message;
					if (!failed) failed = [];

					if (failed.length && !r._server_messages) {
						dataent.throw(__('Cannot update {0}', [failed.map(f => f.bold ? f.bold(): f).join(', ')]));
					}
					dataent.hide_progress();
				});
			}
		});
	},

	document_type: function(frm) {
		// set field options
		if(!frm.doc.document_type) return;

		dataent.model.with_doctype(frm.doc.document_type, function() {
			var options = $.map(dataent.get_meta(frm.doc.document_type).fields,
				function(d) {
					if(d.fieldname && dataent.model.no_value_type.indexOf(d.fieldtype)===-1) {
						return d.fieldname;
					}
					return null;
				}
			);
			frm.set_df_property('field', 'options', options);
		});
	}
});
