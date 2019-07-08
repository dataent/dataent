// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.provide('dataent.datetime');

dataent.defaultDateFormat = "YYYY-MM-DD";
dataent.defaultTimeFormat = "HH:mm:ss";
dataent.defaultDatetimeFormat = dataent.defaultDateFormat + " " + dataent.defaultTimeFormat;
moment.defaultFormat = dataent.defaultDateFormat;

dataent.provide("dataent.datetime");

$.extend(dataent.datetime, {
	convert_to_user_tz: function(date, format) {
		// format defaults to true
		if(dataent.sys_defaults.time_zone) {
			var date_obj = moment.tz(date, dataent.sys_defaults.time_zone).local();
		} else {
			var date_obj = moment(date);
		}

		return (format===false) ? date_obj : date_obj.format(dataent.defaultDatetimeFormat);
	},

	convert_to_system_tz: function(date, format) {
		// format defaults to true

		if(dataent.sys_defaults.time_zone) {
			var date_obj = moment(date).tz(dataent.sys_defaults.time_zone);
		} else {
			var date_obj = moment(date);
		}

		return (format===false) ? date_obj : date_obj.format(dataent.defaultDatetimeFormat);
	},

	is_timezone_same: function() {
		if(dataent.sys_defaults.time_zone) {
			return moment().tz(dataent.sys_defaults.time_zone).utcOffset() === moment().utcOffset();
		} else {
			return true;
		}
	},

	str_to_obj: function(d) {
		return moment(d, dataent.defaultDatetimeFormat)._d;
	},

	obj_to_str: function(d) {
		return moment(d).locale("en").format();
	},

	obj_to_user: function(d) {
		return moment(d).format(dataent.datetime.get_user_fmt().toUpperCase());
	},

	get_diff: function(d1, d2) {
		return moment(d1).diff(d2, "days");
	},

	get_hour_diff: function(d1, d2) {
		return moment(d1).diff(d2, "hours");
	},

	get_day_diff: function(d1, d2) {
		return moment(d1).diff(d2, "days");
	},

	add_days: function(d, days) {
		return moment(d).add(days, "days").format();
	},

	add_months: function(d, months) {
		return moment(d).add(months, "months").format();
	},

	month_start: function() {
		return moment().startOf("month").format();
	},

	month_end: function() {
		return moment().endOf("month").format();
	},

	year_start: function(){
		return moment().startOf("year").format();
	},

	year_end: function(){
		return moment().endOf("year").format();
	},

	get_user_fmt: function() {
		return dataent.sys_defaults && dataent.sys_defaults.date_format || "yyyy-mm-dd";
	},

	str_to_user: function(val, only_time = false) {
		if(!val) return "";

		if(only_time) {
			return moment(val, dataent.defaultTimeFormat)
				.format(dataent.defaultTimeFormat);
		}

		var user_fmt = dataent.datetime.get_user_fmt().toUpperCase();
		if(typeof val !== "string" || val.indexOf(" ")===-1) {
			return moment(val).format(user_fmt);
		} else {
			return moment(val, "YYYY-MM-DD HH:mm:ss").format(user_fmt + " HH:mm:ss");
		}
	},

	get_datetime_as_string: function(d) {
		return moment(d).format("YYYY-MM-DD HH:mm:ss");
	},

	user_to_str: function(val, only_time = false) {

		if(only_time) {
			return moment(val, dataent.defaultTimeFormat)
				.format(dataent.defaultTimeFormat);
		}

		var user_fmt = dataent.datetime.get_user_fmt().toUpperCase();
		var system_fmt = "YYYY-MM-DD";

		if(val.indexOf(" ")!==-1) {
			user_fmt += " HH:mm:ss";
			system_fmt += " HH:mm:ss";
		}

		// user_fmt.replace("YYYY", "YY")? user might only input 2 digits of the year, which should also be parsed
		return moment(val, [user_fmt.replace("YYYY", "YY"),
			user_fmt]).locale("en").format(system_fmt);
	},

	user_to_obj: function(d) {
		return dataent.datetime.str_to_obj(dataent.datetime.user_to_str(d));
	},

	global_date_format: function(d) {
		var m = moment(d);
		if(m._f && m._f.indexOf("HH")!== -1) {
			return m.format("Do MMMM YYYY, h:mma")
		} else {
			return m.format('Do MMMM YYYY');
		}
	},

	now_date: function(as_obj = false) {
		return dataent.datetime._date(dataent.defaultDateFormat, as_obj);
	},

	now_time: function(as_obj = false) {
		return dataent.datetime._date(dataent.defaultTimeFormat, as_obj);
	},

	now_datetime: function(as_obj = false) {
		return dataent.datetime._date(dataent.defaultDatetimeFormat, as_obj);
	},

	_date: function(format, as_obj = false) {
		const time_zone = dataent.sys_defaults && dataent.sys_defaults.time_zone;
		let date;
		if (time_zone) {
			date = moment.tz(time_zone);
		} else {
			date = moment();
		}
		if (as_obj) {
			return dataent.datetime.moment_to_date_obj(date);
		} else {
			return date.format(format);
		}
	},

	moment_to_date_obj: function(moment) {
		const date_obj = new Date();
		const date_array = moment.toArray();
		date_obj.setFullYear(date_array[0]);
		date_obj.setMonth(date_array[1]);
		date_obj.setDate(date_array[2]);
		date_obj.setHours(date_array[3]);
		date_obj.setMinutes(date_array[4]);
		date_obj.setSeconds(date_array[5]);
		date_obj.setMilliseconds(date_array[6]);
		return date_obj;
	},

	nowdate: function() {
		return dataent.datetime.now_date();
	},

	get_today: function() {
		return dataent.datetime.now_date();
	},

	validate: function(d) {
		return moment(d, [
			dataent.defaultDateFormat,
			dataent.defaultDatetimeFormat,
			dataent.defaultTimeFormat
		], true).isValid();
	},

});

// Proxy for dateutil and get_today
Object.defineProperties(window, {
	'dateutil': {
		get: function() {
			console.warn('Please use `dataent.datetime` instead of `dateutil`. It will be deprecated soon.');
			return dataent.datetime;
		}
	},
	'date': {
		get: function() {
			console.warn('Please use `dataent.datetime` instead of `date`. It will be deprecated soon.');
			return dataent.datetime;
		}
	},
	'get_today': {
		get: function() {
			console.warn('Please use `dataent.datetime.get_today` instead of `get_today`. It will be deprecated soon.');
			return dataent.datetime.get_today;
		}
	}
});
