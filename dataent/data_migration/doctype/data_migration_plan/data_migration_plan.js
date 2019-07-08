// Copyright (c) 2017, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.ui.form.on('Data Migration Plan', {
	onload(frm) {
		frm.add_custom_button(__('Run'), () => dataent.new_doc('Data Migration Run', {
			data_migration_plan: frm.doc.name
		}));
	}
});
