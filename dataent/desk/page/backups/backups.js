dataent.pages['backups'].on_page_load = function(wrapper) {
	var page = dataent.ui.make_app_page({
		parent: wrapper,
		title: 'Download Backups',
		single_column: true
	});

	page.add_inner_button(__("Set Number of Backups"), function () {
		dataent.set_route('Form', 'System Settings');
	});

	page.add_inner_button(__("Download Files Backup"), function () {
		dataent.call({
			method:"dataent.desk.page.backups.backups.schedule_files_backup",
			args: {"user_email": dataent.session.user_email}
		});
	});

	dataent.breadcrumbs.add("Setup");

	$(dataent.render_template("backups")).appendTo(page.body.addClass("no-border"));
}
