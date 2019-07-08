dataent.ui.form.on("Version", "refresh", function(frm) {
	$(dataent.render_template('version_view', {doc:frm.doc, data:JSON.parse(frm.doc.data)}))
		.appendTo(frm.fields_dict.table_html.$wrapper.empty());

	frm.add_custom_button(__('Show all Versions'), function() {
		dataent.set_route('List', 'Version',
			{ref_doctype: frm.doc.ref_doctype, docname: frm.doc.docname});
	});
});
