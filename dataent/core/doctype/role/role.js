// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.ui.form.on('Role', {
	refresh: function(frm) {
		frm.add_custom_button("Role Permissions Manager", function() {
			dataent.route_options = {"role": frm.doc.name};
			dataent.set_route("permission-manager");
		});
		frm.add_custom_button("Show Users", function() {
			dataent.route_options = {"role": frm.doc.name};
			dataent.set_route("List", "User", "Report");
		});
	}
});
