dataent.ui.form.on("System Settings", "refresh", function(frm) {
	dataent.call({
		method: "dataent.core.doctype.system_settings.system_settings.load",
		callback: function(data) {
			dataent.all_timezones = data.message.timezones;
			frm.set_df_property("time_zone", "options", dataent.all_timezones);

			$.each(data.message.defaults, function(key, val) {
				frm.set_value(key, val);
				dataent.sys_defaults[key] = val;
			})
		}
	});
});

dataent.ui.form.on("System Settings", "enable_password_policy", function(frm) {
	if(frm.doc.enable_password_policy == 0){
		frm.set_value("minimum_password_score", "");
	} else {
		frm.set_value("minimum_password_score", "2");
	}
});

dataent.ui.form.on("System Settings", "enable_two_factor_auth", function(frm) {
	if(frm.doc.enable_two_factor_auth == 0){
		frm.set_value("bypass_2fa_for_retricted_ip_users", 0);
		frm.set_value("bypass_restrict_ip_check_if_2fa_enabled", 0);
	}
});
