dataent.preview_email = function(template, args, header) {
	dataent.call({
		method: 'dataent.email.email_body.get_email_html',
		args: {
			subject: 'Test',
			template,
			args,
			header
		}
	}).then((r) => {
		var html = r.message;
		html = html.replace(/embed=/, 'src=');
		var d = dataent.msgprint(html);
		d.$wrapper.find('.modal-dialog').css('width', '70%');
	});
};
