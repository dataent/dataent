dataent.ui.form.ControlTime = dataent.ui.form.ControlData.extend({
	make_input: function() {
		var me = this;
		this._super();
		this.$input.datepicker({
			language: "en",
			timepicker: true,
			onlyTimepicker: true,
			timeFormat: "hh:ii:ss",
			startDate: dataent.datetime.now_time(true),
			onSelect: function() {
				// ignore micro seconds
				if (moment(me.get_value(), 'hh:mm:ss').format('HH:mm:ss') != moment(me.value, 'hh:mm:ss').format('HH:mm:ss')) {
					me.$input.trigger('change');
				}				
			},
			onShow: function() {
				$('.datepicker--button:visible').text(__('Now'));
			},
			keyboardNav: false,
			todayButton: true
		});
		this.datepicker = this.$input.data('datepicker');
		this.datepicker.$datepicker
			.find('[data-action="today"]')
			.click(() => {
				this.datepicker.selectDate(dataent.datetime.now_time(true));
			});
		this.refresh();
	},
	set_input: function(value) {
		this._super(value);
		if(value
			&& ((this.last_value && this.last_value !== this.value)
				|| (!this.datepicker.selectedDates.length))) {

			var date_obj = dataent.datetime.moment_to_date_obj(moment(value, 'HH:mm:ss'));
			this.datepicker.selectDate(date_obj);
		}
	},
	set_description: function() {
		const { description } = this.df;
		const { time_zone } = dataent.sys_defaults;
		if (!dataent.datetime.is_timezone_same()) {
			if (!description) {
				this.df.description = time_zone;
			} else if (!description.includes(time_zone)) {
				this.df.description += '<br>' + time_zone;
			}
		}
		this._super();
	}
});
