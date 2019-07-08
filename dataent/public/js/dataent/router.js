// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// route urls to their virtual pages

// re-route map (for rename)
dataent.re_route = {"#login": ""};
dataent.route_titles = {};
dataent.route_flags = {};
dataent.route_history = [];
dataent.view_factory = {};
dataent.view_factories = [];
dataent.route_options = null;

dataent.route = function() {
	if(dataent.re_route[window.location.hash] !== undefined) {
		// after saving a doc, for example,
		// "New DocType 1" and the renamed "TestDocType", both exist in history
		// now if we try to go back,
		// it doesn't allow us to go back to the one prior to "New DocType 1"
		// Hence if this check is true, instead of changing location hash,
		// we just do a back to go to the doc previous to the "New DocType 1"
		var re_route_val = dataent.get_route_str(dataent.re_route[window.location.hash]);
		var cur_route_val = dataent.get_route_str(dataent._cur_route);
		if (decodeURIComponent(re_route_val) === decodeURIComponent(cur_route_val)) {
			window.history.back();
			return;
		} else {
			window.location.hash = dataent.re_route[window.location.hash];
		}
	}

	dataent._cur_route = window.location.hash;

	var route = dataent.get_route();
	if (route === false) {
		return;
	}

	dataent.route_history.push(route);

	if(route[0]) {
		const title_cased_route = dataent.utils.to_title_case(route[0]);

		if(route[1] && dataent.views[title_cased_route + "Factory"]) {
			// has a view generator, generate!
			if(!dataent.view_factory[title_cased_route]) {
				dataent.view_factory[title_cased_route] = new dataent.views[title_cased_route + "Factory"]();
			}

			dataent.view_factory[title_cased_route].show();
		} else {
			// show page
			const route_name = dataent.utils.xss_sanitise(route[0]);
			dataent.views.pageview.show(route_name);
		}
	} else {
		// Show desk
		dataent.views.pageview.show('');
	}


	if(dataent.route_titles[window.location.hash]) {
		dataent.utils.set_title(dataent.route_titles[window.location.hash]);
	} else {
		setTimeout(function() {
			dataent.route_titles[dataent.get_route_str()] = dataent._original_title || document.title;
		}, 1000);
	}

	if(window.mixpanel) {
		window.mixpanel.track(route.slice(0, 2).join(' '));
	}
}

dataent.get_route = function(route) {
	// for app
	route = dataent.get_raw_route_str(route).split('/');
	route = $.map(route, dataent._decode_str);
	var parts = null;
	var doc_name = route[route.length - 1];
	// if the last part contains ? then check if it is valid query string
	if(doc_name.indexOf("?") < doc_name.indexOf("=")){
		parts = doc_name.split("?");
		route[route.length - 1] = parts[0];
	} else {
		parts = doc_name;
	}
	if (parts.length > 1) {
		var query_params = dataent.utils.get_query_params(parts[1]);
		dataent.route_options = $.extend(dataent.route_options || {}, query_params);
	}

	// backward compatibility
	if (route && route[0]==='Module') {
		dataent.set_route('modules', route[1]);
		return false;
	}

	return route;
}

dataent.get_prev_route = function() {
	if(dataent.route_history && dataent.route_history.length > 1) {
		return dataent.route_history[dataent.route_history.length - 2];
	} else {
		return [];
	}
}

dataent._decode_str = function(r) {
	try {
		return decodeURIComponent(r);
	} catch(e) {
		if (e instanceof URIError) {
			return r;
		} else {
			throw e;
		}
	}
}

dataent.get_raw_route_str = function(route) {
	if(!route)
		route = window.location.hash;

	if(route.substr(0,1)=='#') route = route.substr(1);
	if(route.substr(0,1)=='!') route = route.substr(1);

	return route;
}

dataent.get_route_str = function(route) {
	var rawRoute = dataent.get_raw_route_str()
	route = $.map(rawRoute.split('/'), dataent._decode_str).join('/');

	return route;
}

dataent.set_route = function() {
	return new Promise(resolve => {
		var params = arguments;
		if(params.length===1 && $.isArray(params[0])) {
			params = params[0];
		}
		var route = $.map(params, function(a) {
			if($.isPlainObject(a)) {
				dataent.route_options = a;
				return null;
			} else {
				a = String(a);
				if (a && a.match(/[%'"]/)) {
					// if special chars, then encode
					a = encodeURIComponent(a);
				}
				return a;
			}
		}).join('/');

		window.location.hash = route;

		// Set favicon (app.js)
		dataent.app.set_favicon && dataent.app.set_favicon();
		setTimeout(() => {
			dataent.after_ajax(() => {
				resolve();
			});
		}, 100);
	});
}

dataent.set_re_route = function() {
	var tmp = window.location.hash;
	dataent.set_route.apply(null, arguments);
	dataent.re_route[tmp] = window.location.hash;
};

dataent.has_route_options = function() {
	return Boolean(Object.keys(dataent.route_options || {}).length);
}

dataent._cur_route = null;

$(window).on('hashchange', function() {
	// save the title
	dataent.route_titles[dataent._cur_route] = dataent._original_title || document.title;

	if(window.location.hash==dataent._cur_route)
		return;

	// hide open dialog
	if(window.cur_dialog && cur_dialog.hide_on_page_refresh) {
		cur_dialog.hide();
	}

	dataent.route();

	dataent.route.trigger('change');
});

dataent.utils.make_event_emitter(dataent.route);
