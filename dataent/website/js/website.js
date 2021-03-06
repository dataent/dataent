// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt
/* eslint-disable no-console */

import hljs from './syntax_highlight';

dataent.provide("website");
dataent.provide("dataent.awesome_bar_path");
window.cur_frm = null;

$.extend(dataent, {
	boot: {
		lang: 'en'
	},
	_assets_loaded: [],
	require: async function(links, callback) {
		if (typeof (links) === 'string') {
			links = [links];
		}
		for (let link of links) {
			await this.add_asset_to_head(link);
		}
		callback && callback();
	},
	add_asset_to_head(link) {
		return new Promise(resolve => {
			if (dataent._assets_loaded.includes(link)) return resolve();
			let el;
			if(link.split('.').pop() === 'js') {
				el = document.createElement('script');
				el.type = 'text/javascript';
				el.src = link;
			} else {
				el = document.createElement('link');
				el.type = 'text/css';
				el.rel = 'stylesheet';
				el.href = link;
			}
			document.getElementsByTagName('head')[0].appendChild(el);
			el.onload = () => {
				dataent._assets_loaded.push(link);
				resolve();
			};
		});
	},
	hide_message: function() {
		$('.message-overlay').remove();
	},
	call: function(opts) {
		// opts = {"method": "PYTHON MODULE STRING", "args": {}, "callback": function(r) {}}
		if (typeof arguments[0]==='string') {
			opts = {
				method: arguments[0],
				args: arguments[1],
				callback: arguments[2]
			}
		}

		dataent.prepare_call(opts);
		if(opts.freeze) {
			dataent.freeze();
		}
		return $.ajax({
			type: opts.type || "POST",
			url: "/",
			data: opts.args,
			dataType: "json",
			headers: { "X-Dataent-CSRF-Token": dataent.csrf_token },
			statusCode: opts.statusCode || {
				404: function() {
					dataent.msgprint(__("Not found"));
				},
				403: function() {
					dataent.msgprint(__("Not permitted"));
				},
				200: function(data) {
					if(opts.callback)
						opts.callback(data);
					if(opts.success)
						opts.success(data);
				}
			}
		}).always(function(data) {
			if(opts.freeze) {
				dataent.unfreeze();
			}

			// executed before statusCode functions
			if(data.responseText) {
				try {
					data = JSON.parse(data.responseText);
				} catch (e) {
					data = {};
				}
			}
			dataent.process_response(opts, data);
		});
	},
	prepare_call: function(opts) {
		if(opts.btn) {
			$(opts.btn).prop("disabled", true);
		}

		if(opts.msg) {
			$(opts.msg).toggle(false);
		}

		if(!opts.args) opts.args = {};

		// method
		if(opts.method) {
			opts.args.cmd = opts.method;
		}

		// stringify
		$.each(opts.args, function(key, val) {
			if(typeof val != "string") {
				opts.args[key] = JSON.stringify(val);
			}
		});

		if(!opts.no_spinner) {
			//NProgress.start();
		}
	},
	process_response: function(opts, data) {
		//if(!opts.no_spinner) NProgress.done();

		if(opts.btn) {
			$(opts.btn).prop("disabled", false);
		}

		if (data._server_messages) {
			var server_messages = JSON.parse(data._server_messages || '[]');
			server_messages = $.map(server_messages, function(v) {
				// temp fix for messages sent as dict
				try {
					return JSON.parse(v).message;
				} catch (e) {
					return v;
				}
			}).join('<br>');

			if(opts.error_msg) {
				$(opts.error_msg).html(server_messages).toggle(true);
			} else {
				dataent.msgprint(server_messages);
			}
		}

		if(data.exc) {
			// if(opts.btn) {
			// 	$(opts.btn).addClass($(opts.btn).is('button') || $(opts.btn).hasClass('btn') ? "btn-danger" : "text-danger");
			// 	setTimeout(function() { $(opts.btn).removeClass("btn-danger text-danger"); }, 1000);
			// }
			try {
				var err = JSON.parse(data.exc);
				if($.isArray(err)) {
					err = err.join("\n");
				}
				console.error ? console.error(err) : console.log(err);
			} catch(e) {
				console.log(data.exc);
			}

		} else{
			// if(opts.btn) {
			// 	$(opts.btn).addClass($(opts.btn).is('button') || $(opts.btn).hasClass('btn') ? "btn-success" : "text-success");
			// 	setTimeout(function() { $(opts.btn).removeClass("btn-success text-success"); }, 1000);
			// }
		}
		if(opts.msg && data.message) {
			$(opts.msg).html(data.message).toggle(true);
		}

		if(opts.always) {
			opts.always(data);
		}
	},
	show_message: function(text, icon) {
		if(!icon) icon="fa fa-refresh fa-spin";
		dataent.hide_message();
		$('<div class="message-overlay"></div>')
			.html('<div class="content"><i class="'+icon+' text-muted"></i><br>'
				+text+'</div>').appendTo(document.body);
	},
	get_sid: function() {
		var sid = dataent.get_cookie("sid");
		return sid && sid !== "Guest";
	},
	send_message: function(opts, btn) {
		return dataent.call({
			type: "POST",
			method: "dataent.www.contact.send_message",
			btn: btn,
			args: opts,
			callback: opts.callback
		});
	},
	has_permission: function(doctype, docname, perm_type, callback) {
		return dataent.call({
			type: "GET",
			method: "dataent.client.has_permission",
			no_spinner: true,
			args: {doctype: doctype, docname: docname, perm_type: perm_type},
			callback: function(r) {
				if(!r.exc && r.message.has_permission) {
					if(callback) {
						return callback(r);
					}
				}
			}
		});
	},
	render_user: function() {
		var sid = dataent.get_cookie("sid");
		if(sid && sid!=="Guest") {
			$(".btn-login-area").toggle(false);
			$(".logged-in").toggle(true);
			$(".full-name").html(dataent.get_cookie("full_name"));
			$(".user-image").attr("src", dataent.get_cookie("user_image"));

			$('.user-image-wrapper').html(dataent.avatar(null, 'avatar-small'));
			$('.user-image-sidebar').html(dataent.avatar(null, 'avatar-small'));
			$('.user-image-myaccount').html(dataent.avatar(null, 'avatar-large'));
		}
	},
	freeze_count: 0,
	freeze: function(msg) {
		// blur
		if(!$('#freeze').length) {
			var freeze = $('<div id="freeze" class="modal-backdrop fade"></div>')
				.appendTo("body");

			freeze.html(repl('<div class="freeze-message-container"><div class="freeze-message">%(msg)s</div></div>',
				{msg: msg || ""}));

			setTimeout(function() {
				freeze.addClass("in");
			}, 1);

		} else {
			$("#freeze").addClass("in");
		}
		dataent.freeze_count++;
	},
	unfreeze: function() {
		if(!dataent.freeze_count) return; // anything open?
		dataent.freeze_count--;
		if(!dataent.freeze_count) {
			var freeze = $('#freeze').removeClass("in");
			setTimeout(function() {
				if(!dataent.freeze_count) {
					freeze.remove();
				}
			}, 150);
		}
	},

	trigger_ready: function() {
		dataent.ready_events.forEach(function(fn) {
			fn();
		});
	},

	highlight_code_blocks: function() {
		hljs.initHighlighting();
	},
	bind_filters: function() {
		// set in select
		$(".filter").each(function() {
			var key = $(this).attr("data-key");
			var val = dataent.utils.get_url_arg(key).replace(/\+/g, " ");

			if(val) $(this).val(val);
		});

		// search url
		var search = function() {
			var args = {};
			$(".filter").each(function() {
				var val = $(this).val();
				if(val) args[$(this).attr("data-key")] = val;
			});

			window.location.href = location.pathname + "?" + $.param(args);
		};

		$(".filter").on("change", function() {
			search();
		});
	},
	bind_navbar_search: function() {
		dataent.get_navbar_search().on("keypress", function(e) {
			var val = $(this).val();
			if(e.which===13 && val) {
				$(this).val("").blur();
				dataent.do_search(val);
				return false;
			}
		});
	},
	do_search: function(val) {
		var path = (dataent.awesome_bar_path && dataent.awesome_bar_path[location.pathname]
			|| window.search_path || location.pathname);

		window.location.href = path + "?txt=" + encodeURIComponent(val);
	},
	set_search_path: function(path) {
		dataent.awesome_bar_path[location.pathname] = path;
	},
	make_navbar_active: function() {
		var pathname = window.location.pathname;
		$(".navbar-nav a.active").removeClass("active");
		$(".navbar-nav a").each(function() {
			var href = $(this).attr("href");
			if(href===pathname) {
				$(this).addClass("active");
				return false;
			}
		});
	},
	get_navbar_search: function() {
		return $(".navbar .search, .sidebar .search");
	},
	is_user_logged_in: function() {
		return dataent.get_cookie("sid") && dataent.get_cookie("sid") !== "Guest";
	},
	add_switch_to_desk: function() {
		$('.switch-to-desk').removeClass('hidden');
	}
});


// Utility functions

window.valid_email = function(id) {
	// eslint-disable-next-line
	return /[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?/.test(id.toLowerCase());
}

window.validate_email = valid_email;

window.cstr = function(s) {
	return s==null ? '' : s+'';
}

window.is_null = function is_null(v) {
	if(v===null || v===undefined || cstr(v).trim()==="") return true;
};

window.is_html = function is_html(txt) {
	if(txt.indexOf("<br>")==-1 && txt.indexOf("<p")==-1
		&& txt.indexOf("<img")==-1 && txt.indexOf("<div")==-1) {
		return false;
	}
	return true;
};

window.ask_to_login = function ask_to_login() {
	if(!dataent.is_user_logged_in()) {
		if(localStorage) {
			localStorage.setItem("last_visited",
				window.location.href.replace(window.location.origin, ""));
		}
		window.location.href = "login";
	}
};

// check if logged in?
$(document).ready(function() {
	window.full_name = dataent.get_cookie("full_name");
	var logged_in = dataent.is_user_logged_in();
	$("#website-login").toggleClass("hide", logged_in ? true : false);
	$("#website-post-login").toggleClass("hide", logged_in ? false : true);
	$(".logged-in").toggleClass("hide", logged_in ? false : true);

	dataent.bind_navbar_search();

	// switch to app link
	if(dataent.get_cookie("system_user")==="yes" && logged_in) {
		dataent.add_switch_to_desk();
	}

	dataent.render_user();

	$(document).trigger("page-change");
});

$(document).on("page-change", function() {
	$(document).trigger("apply_permissions");
	$('.dropdown-toggle').dropdown();

	//multilevel dropdown fix
	$('.dropdown-menu .dropdown-submenu .dropdown-toggle').on('click', function(e) {
		e.stopPropagation();
		$(this).parent().parent().parent().addClass('open');
	});

	$.extend(dataent, dataent.get_cookies());
	dataent.session = {'user': dataent.user_id};

	dataent.datetime.refresh_when();
	dataent.trigger_ready();
	dataent.bind_filters();
	dataent.highlight_code_blocks();
	dataent.make_navbar_active();
	// scroll to hash
	if (window.location.hash) {
		var element = document.getElementById(window.location.hash.substring(1));
		element && element.scrollIntoView(true);
	}

});


dataent.ready(function() {
	dataent.call({
		method: 'dataent.website.doctype.website_settings.website_settings.is_chat_enabled',
		callback: (r) => {
			if (r.message) {
				dataent.require('/assets/js/moment-bundle.min.js', () => {
					dataent.require('/assets/js/chat.js', () => {
						dataent.chat.setup();
					});
				});
			}
		}
	});
	dataent.socketio.init(window.socketio_port);
});
