// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// My HTTP Request

dataent.provide('dataent.request');
dataent.provide('dataent.request.error_handlers');
dataent.request.url = '/';
dataent.request.ajax_count = 0;
dataent.request.waiting_for_ajax = [];

dataent.xcall = function(method, params) {
	return new Promise((resolve, reject) => {
		dataent.call({
			method: method,
			args: params,
			callback: (r) => {
				resolve(r.message);
			},
			error: (r) => {
				reject(r.message);
			}
		});
	});
};

// generic server call (call page, object)
dataent.call = function(opts) {
	if (!dataent.is_online()) {
		dataent.show_alert({
			indicator: 'orange',
			message: __('You are not connected to Internet. Retry after sometime.')
		}, 3);
		opts.always && opts.always();
		return $.ajax();
	}
	if (typeof arguments[0]==='string') {
		opts = {
			method: arguments[0],
			args: arguments[1],
			callback: arguments[2]
		}
	}

	if(opts.quiet) {
		opts.no_spinner = true;
	}
	var args = $.extend({}, opts.args);

	// cmd
	if(opts.module && opts.page) {
		args.cmd = opts.module+'.page.'+opts.page+'.'+opts.page+'.'+opts.method;
	} else if(opts.doc) {
		$.extend(args, {
			cmd: "runserverobj",
			docs: dataent.get_doc(opts.doc.doctype, opts.doc.name),
			method: opts.method,
			args: opts.args,
		});
	} else if(opts.method) {
		args.cmd = opts.method;
	}

	var callback = function(data, response_text) {
		if(data.task_id) {
			// async call, subscribe
			dataent.socketio.subscribe(data.task_id, opts);

			if(opts.queued) {
				opts.queued(data);
			}
		}
		else if (opts.callback) {
			// ajax
			return opts.callback(data, response_text);
		}
	}

	return dataent.request.call({
		type: opts.type || "POST",
		args: args,
		success: callback,
		error: opts.error,
		always: opts.always,
		btn: opts.btn,
		freeze: opts.freeze,
		freeze_message: opts.freeze_message,
		// show_spinner: !opts.no_spinner,
		async: opts.async,
		url: opts.url || dataent.request.url,
	});
}


dataent.request.call = function(opts) {
	dataent.request.prepare(opts);

	var statusCode = {
		200: function(data, xhr) {
			opts.success_callback && opts.success_callback(data, xhr.responseText);
		},
		401: function(xhr) {
			if(dataent.app.session_expired_dialog && dataent.app.session_expired_dialog.display) {
				dataent.app.redirect_to_login();
			} else {
				dataent.app.handle_session_expired();
			}
		},
		404: function(xhr) {
			dataent.msgprint({title:__("Not found"), indicator:'red',
				message: __('The resource you are looking for is not available')});
		},
		403: function(xhr) {
			if (dataent.get_cookie('sid')==='Guest') {
				// session expired
				dataent.app.handle_session_expired();
			}
			else if(xhr.responseJSON && xhr.responseJSON._error_message) {
				dataent.msgprint({
					title:__("Not permitted"), indicator:'red',
					message: xhr.responseJSON._error_message
				});

				xhr.responseJSON._server_messages = null;
			}
			else if (xhr.responseJSON && xhr.responseJSON._server_messages) {
				var _server_messages = JSON.parse(xhr.responseJSON._server_messages);

				// avoid double messages
				if (_server_messages.indexOf(__("Not permitted"))!==-1) {
					return;
				}
			}
			else {
				dataent.msgprint({
					title:__("Not permitted"), indicator:'red',
					message: __('You do not have enough permissions to access this resource. Please contact your manager to get access.')});
			}


		},
		508: function(xhr) {
			dataent.utils.play_sound("error");
			dataent.msgprint({title:__('Please try again'), indicator:'red',
				message:__("Another transaction is blocking this one. Please try again in a few seconds.")});
		},
		413: function(data, xhr) {
			dataent.msgprint({indicator:'red', title:__('File too big'), message:__("File size exceeded the maximum allowed size of {0} MB",
				[(dataent.boot.max_file_size || 5242880) / 1048576])});
		},
		417: function(xhr) {
			var r = xhr.responseJSON;
			if (!r) {
				try {
					r = JSON.parse(xhr.responseText);
				} catch (e) {
					r = xhr.responseText;
				}
			}

			opts.error_callback && opts.error_callback(r);
		},
		501: function(data, xhr) {
			if(typeof data === "string") data = JSON.parse(data);
			opts.error_callback && opts.error_callback(data, xhr.responseText);
		},
		500: function(xhr) {
			dataent.utils.play_sound("error");
			dataent.msgprint({message:__("Server Error: Please check your server logs or contact tech support."), title:__('Something went wrong'), indicator: 'red'});
			try {
				opts.error_callback && opts.error_callback();
				dataent.request.report_error(xhr, opts);
			} catch (e) {
				dataent.request.report_error(xhr, opts);
			}
		},
		504: function(xhr) {
			dataent.msgprint(__("Request Timed Out"))
			opts.error_callback && opts.error_callback();
		},
		502: function(xhr) {
			dataent.msgprint(__("Internal Server Error"));
		}
	};

	var ajax_args = {
		url: opts.url || dataent.request.url,
		data: opts.args,
		type: opts.type,
		dataType: opts.dataType || 'json',
		async: opts.async,
		headers: {
			"X-Dataent-CSRF-Token": dataent.csrf_token,
			"Accept": "application/json"
		},
		cache: false
	};

	dataent.last_request = ajax_args.data;

	return $.ajax(ajax_args)
		.done(function(data, textStatus, xhr) {
			try {
				if(typeof data === "string") data = JSON.parse(data);

				// sync attached docs
				if(data.docs || data.docinfo) {
					dataent.model.sync(data);
				}

				// sync translated messages
				if(data.__messages) {
					$.extend(dataent._messages, data.__messages);
				}

				// callbacks
				var status_code_handler = statusCode[xhr.statusCode().status];
				if (status_code_handler) {
					status_code_handler(data, xhr);
				}
			} catch(e) {
				console.log("Unable to handle success response"); // eslint-disable-line
				console.trace(e); // eslint-disable-line
			}

		})
		.always(function(data, textStatus, xhr) {
			try {
				if(typeof data==="string") {
					data = JSON.parse(data);
				}
				if(data.responseText) {
					var xhr = data;
					data = JSON.parse(data.responseText);
				}
			} catch(e) {
				data = null;
				// pass
			}
			dataent.request.cleanup(opts, data);
			if(opts.always) {
				opts.always(data);
			}
		})
		.fail(function(xhr, textStatus) {
			try {
				var status_code_handler = statusCode[xhr.statusCode().status];
				if (status_code_handler) {
					status_code_handler(xhr);
				} else {
					// if not handled by error handler!
					opts.error_callback && opts.error_callback(xhr);
				}
			} catch(e) {
				console.log("Unable to handle failed response"); // eslint-disable-line
				console.trace(e); // eslint-disable-line
			}
		});
}

// call execute serverside request
dataent.request.prepare = function(opts) {
	$("body").attr("data-ajax-state", "triggered");

	// btn indicator
	if(opts.btn) $(opts.btn).prop("disabled", true);

	// freeze page
	if(opts.freeze) dataent.dom.freeze(opts.freeze_message);

	// stringify args if required
	for(var key in opts.args) {
		if(opts.args[key] && ($.isPlainObject(opts.args[key]) || $.isArray(opts.args[key]))) {
			opts.args[key] = JSON.stringify(opts.args[key]);
		}
	}

	// no cmd?
	if(!opts.args.cmd && !opts.url) {
		console.log(opts)
		throw "Incomplete Request";
	}

	opts.success_callback = opts.success;
	opts.error_callback = opts.error;
	delete opts.success;
	delete opts.error;

}

dataent.request.cleanup = function(opts, r) {
	// stop button indicator
	if(opts.btn) {
		$(opts.btn).prop("disabled", false);
	}

	$("body").attr("data-ajax-state", "complete");

	// un-freeze page
	if(opts.freeze) dataent.dom.unfreeze();

	if(r) {

		// session expired? - Guest has no business here!
		if(r.session_expired || dataent.get_cookie("sid")==="Guest") {
			dataent.app.handle_session_expired();
			return;
		}

		// global error handlers
		if (r.exc_type) {
			let handlers = dataent.request.error_handlers[r.exc_type] || [];
			handlers.forEach(handler => {
				handler(r);
			});
		}

		// show messages
		if(r._server_messages && !opts.silent) {
			let handlers = dataent.request.error_handlers[r.exc_type] || [];
			// dont show server messages if their handlers exist
			if (!handlers.length) {
				r._server_messages = JSON.parse(r._server_messages);
				dataent.hide_msgprint();
				dataent.msgprint(r._server_messages);
			}
		}

		// show errors
		if(r.exc) {
			r.exc = JSON.parse(r.exc);
			if(r.exc instanceof Array) {
				$.each(r.exc, function(i, v) {
					if(v) {
						console.log(v);
					}
				})
			} else {
				console.log(r.exc);
			}
		}

		// debug messages
		if(r._debug_messages) {
			if(opts.args) {
				console.log("======== arguments ========");
				console.log(opts.args);
				console.log("========")
			}
			$.each(JSON.parse(r._debug_messages), function(i, v) { console.log(v); });
			console.log("======== response ========");
			delete r._debug_messages;
			console.log(r);
			console.log("========");
		}
	}

	dataent.last_response = r;
}

dataent.after_server_call = () => {
	if(dataent.request.ajax_count) {
		return new Promise(resolve => {
			dataent.request.waiting_for_ajax.push(() => {
				resolve();
			});
		});
	} else {
		return null;
	}
};

dataent.after_ajax = function(fn) {
	return new Promise(resolve => {
		if(dataent.request.ajax_count) {
			dataent.request.waiting_for_ajax.push(() => {
				if(fn) fn();
				resolve();
			});
		} else {
			if(fn) fn();
			resolve();
		}
	});
};

dataent.request.report_error = function(xhr, request_opts) {
	var data = JSON.parse(xhr.responseText);
	var exc;
	if (data.exc) {
		try {
			exc = (JSON.parse(data.exc) || []).join("\n");
		} catch (e) {
			exc = data.exc;
		}
		delete data.exc;
	} else {
		exc = "";
	}

	if (exc) {
		var error_report_email = dataent.boot.error_report_email;
		var error_message = '<div>\
			<pre style="max-height: 300px; margin-top: 7px;">'
				+ exc.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</pre>'
			+'<p class="text-right"><a class="btn btn-primary btn-sm report-btn">'
			+ __("Report this issue") + '</a></p>'
			+'</div>';

		request_opts = dataent.request.cleanup_request_opts(request_opts);

		window.msg_dialog = dataent.msgprint({message:error_message, indicator:'red'});

		msg_dialog.msg_area.find(".report-btn")
			.toggle(error_report_email ? true : false)
			.on("click", function() {
				var error_report_message = [
					'<h5>Please type some additional information that could help us reproduce this issue:</h5>',
					'<div style="min-height: 100px; border: 1px solid #bbb; \
						border-radius: 5px; padding: 15px; margin-bottom: 15px;"></div>',
					'<hr>',
					'<h5>App Versions</h5>',
					'<pre>' + JSON.stringify(dataent.boot.versions, null, "\t") + '</pre>',
					'<h5>Route</h5>',
					'<pre>' + dataent.get_route_str() + '</pre>',
					'<hr>',
					'<h5>Error Report</h5>',
					'<pre>' + exc + '</pre>',
					'<hr>',
					'<h5>Request Data</h5>',
					'<pre>' + JSON.stringify(request_opts, null, "\t") + '</pre>',
					'<hr>',
					'<h5>Response JSON</h5>',
					'<pre>' + JSON.stringify(data, null, '\t')+ '</pre>'
				].join("\n");

				var communication_composer = new dataent.views.CommunicationComposer({
					subject: 'Error Report [' + dataent.datetime.nowdate() + ']',
					recipients: error_report_email,
					message: error_report_message,
					doc: {
						doctype: "User",
						name: dataent.session.user
					}
				});
				communication_composer.dialog.$wrapper.css("z-index", cint(msg_dialog.$wrapper.css("z-index")) + 1);
			});
	}
};

dataent.request.cleanup_request_opts = function(request_opts) {
	var doc = (request_opts.args || {}).doc;
	if (doc) {
		doc = JSON.parse(doc);
		$.each(Object.keys(doc), function(i, key) {
			if (key.indexOf("password")!==-1 && doc[key]) {
				// mask the password
				doc[key] = "*****";
			}
		});
		request_opts.args.doc = JSON.stringify(doc);
	}
	return request_opts;
};

dataent.request.on_error = function(error_type, handler) {
	dataent.request.error_handlers[error_type] = dataent.request.error_handlers[error_type] || [];
	dataent.request.error_handlers[error_type].push(handler);
}

$(document).ajaxSend(function() {
	dataent.request.ajax_count++;
});

$(document).ajaxComplete(function() {
	dataent.request.ajax_count--;
	if(!dataent.request.ajax_count) {
		$.each(dataent.request.waiting_for_ajax || [], function(i, fn) {
			fn();
		});
		dataent.request.waiting_for_ajax = [];
	}
});
