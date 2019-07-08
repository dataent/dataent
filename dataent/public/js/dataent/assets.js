// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// library to mange assets (js, css, models, html) etc in the app.
// will try and get from localStorge if latest are available
// depends on dataent.versions to manage versioning

dataent.require = function(items, callback) {
	if(typeof items === "string") {
		items = [items];
	}
	dataent.assets.execute(items, callback);
};

dataent.assets = {
	check: function() {
		// if version is different then clear localstorage
		if(window._version_number != localStorage.getItem("_version_number")) {
			dataent.assets.clear_local_storage();
			console.log("Cleared App Cache.");
		}

		if(localStorage._last_load) {
			var not_updated_since = new Date() - new Date(localStorage._last_load);
			if(not_updated_since < 10000 || not_updated_since > 86400000) {
				dataent.assets.clear_local_storage();
			}
		} else {
			dataent.assets.clear_local_storage();
		}

		dataent.assets.init_local_storage();
	},

	init_local_storage: function() {
		localStorage._last_load = new Date();
		localStorage._version_number = window._version_number;
		if(dataent.boot) localStorage.metadata_version = dataent.boot.metadata_version;
	},

	clear_local_storage: function() {
		$.each(["_last_load", "_version_number", "metadata_version", "page_info",
			"last_visited"], function(i, key) {
			localStorage.removeItem(key);
		});

		// clear assets
		for(var key in localStorage) {
			if(key.indexOf("desk_assets:")===0 || key.indexOf("_page:")===0
				|| key.indexOf("_doctype:")===0 || key.indexOf("preferred_breadcrumbs:")===0) {
				localStorage.removeItem(key);
			}
		}
		console.log("localStorage cleared");
	},


	// keep track of executed assets
	executed_ : [],

	// pass on to the handler to set
	execute: function(items, callback) {
		var to_fetch = []
		for(var i=0, l=items.length; i<l; i++) {
			if(!dataent.assets.exists(items[i])) {
				to_fetch.push(items[i]);
			}
		}
		if(to_fetch.length) {
			dataent.assets.fetch(to_fetch, function() {
				dataent.assets.eval_assets(items, callback);
			});
		} else {
			dataent.assets.eval_assets(items, callback);
		}
	},

	eval_assets: function(items, callback) {
		for(var i=0, l=items.length; i<l; i++) {
			// execute js/css if not already.
			var path = items[i];
			if(dataent.assets.executed_.indexOf(path)===-1) {
				// execute
				dataent.assets.handler[dataent.assets.extn(path)](dataent.assets.get(path), path);
				dataent.assets.executed_.push(path)
			}
		}
		callback && callback();
	},

	// check if the asset exists in
	// localstorage
	exists: function(src) {
		if(dataent.assets.executed_.indexOf(src)!== -1) {
			return true;
		}
		if(dataent.boot.developer_mode) {
			return false;
		}
		if(dataent.assets.get(src)) {
			return true;
		} else {
			return false;
		}
	},

	// load an asset via
	fetch: function(items, callback) {
		// this is virtual page load, only get the the source
		// *without* the template

		dataent.call({
			type: "GET",
			method:"dataent.client.get_js",
			args: {
				"items": items
			},
			callback: function(r) {
				$.each(items, function(i, src) {
					dataent.assets.add(src, r.message[i]);
				});
				callback();
			},
			freeze: true,
		});
	},

	add: function(src, txt) {
		if('localStorage' in window) {
			try {
				dataent.assets.set(src, txt);
			} catch(e) {
				// if quota is exceeded, clear local storage and set item
				dataent.assets.clear_local_storage();
				dataent.assets.set(src, txt);
			}
		}
	},

	get: function(src) {
		return localStorage.getItem("desk_assets:" + src);
	},

	set: function(src, txt) {
		localStorage.setItem("desk_assets:" + src, txt);
	},

	extn: function(src) {
		if(src.indexOf('?')!=-1) {
			src = src.split('?').slice(-1)[0];
		}
		return src.split('.').slice(-1)[0];
	},

	handler: {
		js: function(txt, src) {
			dataent.dom.eval(txt);
		},
		css: function(txt, src) {
			dataent.dom.set_style(txt);
		}
	},
};
