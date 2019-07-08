

dataent.user_info = function(uid) {
	if(!uid)
		uid = dataent.session.user;

	if(uid.toLowerCase()==="bot") {
		return {
			fullname: __("Bot"),
			image: "/assets/dataent/images/ui/bot.png",
			abbr: "B"
		}
	}

	if(!(dataent.boot.user_info && dataent.boot.user_info[uid])) {
		var user_info = {
			fullname: dataent.utils.capitalize(uid.split("@")[0]) || "Unknown"
		};
	} else {
		var user_info = dataent.boot.user_info[uid];
	}

	user_info.abbr = dataent.get_abbr(user_info.fullname);
	user_info.color = dataent.get_palette(user_info.fullname);

	return user_info;
}

dataent.ui.set_user_background = function(src, selector, style) {
	if(!selector) selector = "#page-desktop";
	if(!style) style = "Fill Screen";
	if(src) {
		if (window.cordova && src.indexOf("http") === -1) {
			src = dataent.base_url + src;
		}
		var background = repl('background: url("%(src)s") center center;', {src: src});
	} else {
		var background = "background-color: #4B4C9D;";
	}

	dataent.dom.set_style(repl('%(selector)s { \
		%(background)s \
		background-attachment: fixed; \
		%(style)s \
	}', {
		selector:selector,
		background:background,
		style: style==="Fill Screen" ? "background-size: cover;" : ""
	}));
}

dataent.provide('dataent.user');

$.extend(dataent.user, {
	name: 'Guest',
	full_name: function(uid) {
		return uid === dataent.session.user ?
			__("You") :
			dataent.user_info(uid).fullname;
	},
	image: function(uid) {
		return dataent.user_info(uid).image;
	},
	abbr: function(uid) {
		return dataent.user_info(uid).abbr;
	},
	has_role: function(rl) {
		if(typeof rl=='string')
			rl = [rl];
		for(var i in rl) {
			if((dataent.boot ? dataent.boot.user.roles : ['Guest']).indexOf(rl[i])!=-1)
				return true;
		}
	},
	get_desktop_items: function() {
		// hide based on permission
		var modules_list = $.map(dataent.boot.desktop_icons, function(icon) {
			var m = icon.module_name;
			var type = dataent.modules[m] && dataent.modules[m].type;

			if(dataent.boot.user.allow_modules.indexOf(m) === -1) return null;

			var ret = null;
			if (type === "module") {
				if(dataent.boot.user.allow_modules.indexOf(m)!=-1 || dataent.modules[m].is_help)
					ret = m;
			} else if (type === "page") {
				if(dataent.boot.allowed_pages.indexOf(dataent.modules[m].link)!=-1)
					ret = m;
			} else if (type === "list") {
				if(dataent.model.can_read(dataent.modules[m]._doctype))
					ret = m;
			} else if (type === "view") {
				ret = m;
			} else if (type === "setup") {
				if(dataent.user.has_role("System Manager") || dataent.user.has_role("Administrator"))
					ret = m;
			} else {
				ret = m;
			}

			return ret;
		});

		return modules_list;
	},

	is_module: function(m) {
		var icons = dataent.get_desktop_icons();
		for(var i=0; i<icons.length; i++) {
			if(m===icons[i].module_name) return true;
		}
		return false;
	},

	is_report_manager: function() {
		return dataent.user.has_role(['Administrator', 'System Manager', 'Report Manager']);
	},

	get_formatted_email: function(email) {
		var fullname = dataent.user.full_name(email);

		if (!fullname) {
			return email;
		} else {
			// to quote or to not
			var quote = '';

			// only if these special characters are found
			// why? To make the output same as that in python!
			if (fullname.search(/[\[\]\\()<>@,:;".]/) !== -1) {
				quote = '"';
			}

			return repl('%(quote)s%(fullname)s%(quote)s <%(email)s>', {
				fullname: fullname,
				email: email,
				quote: quote
			});
		}
	},

	get_emails: ( ) => {
		return Object.keys(dataent.boot.user_info).map(key => dataent.boot.user_info[key].email);
	},

	/* Normally dataent.user is an object
	 * having properties and methods.
	 * But in the following case
	 * 
	 * if (dataent.user === 'Administrator')
	 * 
	 * dataent.user will cast to a string
	 * returning dataent.user.name
	 */
	toString: function() {
		return this.name;
	}
});

dataent.session_alive = true;
$(document).bind('mousemove', function() {
	if(dataent.session_alive===false) {
		$(document).trigger("session_alive");
	}
	dataent.session_alive = true;
	if(dataent.session_alive_timeout)
		clearTimeout(dataent.session_alive_timeout);
	dataent.session_alive_timeout = setTimeout('dataent.session_alive=false;', 30000);
});