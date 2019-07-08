dataent.provide("dataent.integration_service");

dataent.integration_service.gsuite = {
	create_gsuite_file: function(args, opts) {
		return dataent.call({
			type:'POST',
			method: 'dataent.integrations.doctype.gsuite_templates.gsuite_templates.create_gsuite_doc',
			args: args,
			callback: function(r) {
				var attachment = r.message;
				opts.callback && opts.callback(attachment, r);
			}
		});
	}
};
