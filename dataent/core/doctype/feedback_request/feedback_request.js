// Copyright (c) 2016, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.ui.form.on('Feedback Request', {
	refresh: function(frm) {
		var rating_icons = dataent.render_template("rating_icons", {rating: frm.doc.rating, show_label: false});
		$(frm.fields_dict.feedback_rating.wrapper).html(rating_icons);

		if(frm.doc.reference_doctype && frm.doc.reference_name) {
			frm.add_custom_button(__(frm.doc.reference_name), function() {
				dataent.set_route("Form", frm.doc.reference_doctype, frm.doc.reference_name);
			});
		}

		if(frm.doc.reference_communication){
			frm.add_custom_button(__("Communication"), function() {
				dataent.set_route("Form", "Communication", frm.doc.reference_communication);
			});
		}
	}
});
