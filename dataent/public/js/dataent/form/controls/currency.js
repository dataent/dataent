dataent.ui.form.ControlCurrency = dataent.ui.form.ControlFloat.extend({
	format_for_input: function(value) {
		var formatted_value = format_number(parseFloat(value), this.get_number_format(), this.get_precision());
		return isNaN(parseFloat(value)) ? "" : formatted_value;
	},

	get_precision: function() {
		// always round based on field precision or currency's precision
		// this method is also called in this.parse()
		if (!this.df.precision) {
			if(dataent.boot.sysdefaults.currency_precision) {
				this.df.precision = dataent.boot.sysdefaults.currency_precision;
			} else {
				this.df.precision = get_number_format_info(this.get_number_format()).precision;
			}
		}

		return this.df.precision;
	}
});
