dataent.ui.form.ControlText = dataent.ui.form.ControlData.extend({
	html_element: "textarea",
	horizontal: false,
	make_wrapper: function() {
		this._super();
		this.$wrapper.find(".like-disabled-input").addClass("for-description");
	},
	make_input: function() {
		this._super();
		this.$input.css({'height': '300px'});
	}
});

dataent.ui.form.ControlLongText = dataent.ui.form.ControlText;
dataent.ui.form.ControlSmallText = dataent.ui.form.ControlText.extend({
	make_input: function() {
		this._super();
		this.$input.css({'height': '150px'});
	}
});
