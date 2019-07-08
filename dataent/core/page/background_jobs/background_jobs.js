dataent.pages['background_jobs'].on_page_load = function(wrapper) {
	var page = dataent.ui.make_app_page({
		parent: wrapper,
		title: 'Background Jobs',
		single_column: true
	});

	$(dataent.render_template('background_jobs_outer')).appendTo(page.body);
	page.content = $(page.body).find('.table-area');

	dataent.pages.background_jobs.page = page;
}

dataent.pages['background_jobs'].on_page_show = function(wrapper) {
	dataent.pages.background_jobs.refresh_jobs();
}

dataent.pages.background_jobs.refresh_jobs = function() {
	var page = dataent.pages.background_jobs.page;

	// don't call if already waiting for a response
	if(page.called) return;
	page.called = true;
	dataent.call({
		method: 'dataent.core.page.background_jobs.background_jobs.get_info',
		args: {
			show_failed: page.body.find('.show-failed').prop('checked') ? 1 : 0
		},
		callback: function(r) {
			page.called = false;
			page.body.find('.list-jobs').remove();
			$(dataent.render_template('background_jobs', {jobs:r.message || []})).appendTo(page.content);

			if(dataent.get_route()[0]==='background_jobs') {
				dataent.background_jobs_timeout = setTimeout(dataent.pages.background_jobs.refresh_jobs, 2000);
			}
		}
	});
}
