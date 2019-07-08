// Copyright (c) 2017, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.ui.form.on('Print Style', {
	refresh: function(frm) {
		frm.add_custom_button(__('Print Settings'), () => {
			dataent.set_route('Form', 'Print Settings');
		})
	}
});
