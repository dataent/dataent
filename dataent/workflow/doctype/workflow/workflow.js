dataent.provide("dataent.core")

dataent.ui.form.on("Workflow", {
	onload: function(frm) {
		frm.set_query("document_type", {"issingle": 0, "istable": 0});
	},
	refresh: function(frm) {
		frm.events.update_field_options(frm);
	},
	document_type: function(frm) {
		frm.events.update_field_options(frm);
	},
	update_field_options: function(frm) {
		var doc = frm.doc;
		if (doc.document_type) {
			const get_field_method = 'dataent.workflow.doctype.workflow.workflow.get_fieldnames_for';
			dataent.xcall(get_field_method, { doctype: doc.document_type })
				.then(resp => {
					dataent.meta.get_docfield("Workflow Document State", "update_field", frm.doc.name).options = [""].concat(resp);
				})
		}
	}
})

