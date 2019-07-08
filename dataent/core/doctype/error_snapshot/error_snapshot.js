dataent.ui.form.on("Error Snapshot", "load", function(frm){
	frm.set_read_only(true);
});

dataent.ui.form.on("Error Snapshot", "refresh", function(frm){
	frm.set_df_property("view", "options", dataent.render_template("error_snapshot", {"doc": frm.doc}));

	if (frm.doc.relapses) {
		frm.add_custom_button(__('Show Relapses'), function() {
			dataent.route_options = {
				parent_error_snapshot: frm.doc.name
			};
			dataent.set_route("List", "Error Snapshot");
		});
	}
});
