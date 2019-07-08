/* eslint semi: "never" */
dataent.ui.form.on('Chat Profile', {
	refresh: function (form) {
		if ( form.doc.name !== dataent.session.user ) {
			form.disable_save()
			form.set_read_only(true)
			// There's one more that faris@epaas.xyz told me to add here. form.refresh_fields()?
		}
	}
});
