// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.breadcrumbs = {
	all: {},

	preferred: {
		"File": ""
	},

	set_doctype_module: function(doctype, module) {
		localStorage["preferred_breadcrumbs:" + doctype] = module;
	},

	get_doctype_module: function(doctype) {
		return localStorage["preferred_breadcrumbs:" + doctype];
	},

	add: function(module, doctype, type) {
		let obj;
		if (typeof module === 'object') {
			obj = module;
		} else {
			obj = {
				module:module,
				doctype:doctype,
				type:type
			}
		}

		dataent.breadcrumbs.all[dataent.breadcrumbs.current_page()] = obj;
		dataent.breadcrumbs.update();
	},

	current_page: function() {
		return dataent.get_route_str();
	},

	update: function() {
		var breadcrumbs = dataent.breadcrumbs.all[dataent.breadcrumbs.current_page()];

		if(!dataent.visible_modules) {
			dataent.visible_modules = $.map(dataent.get_desktop_icons(true), (m) => { return m.module_name; });
		}

		var $breadcrumbs = $("#navbar-breadcrumbs").empty();

		if(!breadcrumbs) {
			$("body").addClass("no-breadcrumbs");
			return;
		}

		if (breadcrumbs.type === 'Custom') {
			const html = `<li><a href="${breadcrumbs.route}">${breadcrumbs.label}</a></li>`;
			$breadcrumbs.append(html);
			$("body").removeClass("no-breadcrumbs");
			return;
		}

		// get preferred module for breadcrumbs, based on sent via module
		var from_module = dataent.breadcrumbs.get_doctype_module(breadcrumbs.doctype);

		if(from_module) {
			breadcrumbs.module = from_module;
		} else if(dataent.breadcrumbs.preferred[breadcrumbs.doctype]!==undefined) {
			// get preferred module for breadcrumbs
			breadcrumbs.module = dataent.breadcrumbs.preferred[breadcrumbs.doctype];
		}

		if(breadcrumbs.module) {
			if(in_list(["Core", "Email", "Custom", "Workflow", "Print"], breadcrumbs.module)) {
				breadcrumbs.module = "Setup";
			}

			if(dataent.get_module(breadcrumbs.module)) {
				// if module access exists
				var module_info = dataent.get_module(breadcrumbs.module),
					icon = module_info && module_info.icon,
					label = module_info ? module_info.label : breadcrumbs.module;


				if(module_info && !module_info.blocked && dataent.visible_modules.includes(module_info.module_name)) {
					$(repl('<li><a href="#modules/%(module)s">%(label)s</a></li>',
						{ module: breadcrumbs.module, label: __(label) }))
						.appendTo($breadcrumbs);
				}
			}
		}
		if(breadcrumbs.doctype && dataent.get_route()[0]==="Form") {
			if(breadcrumbs.doctype==="User"
				&& dataent.user.is_module("Setup")===-1
				|| dataent.get_doc('DocType', breadcrumbs.doctype).issingle) {
				// no user listview for non-system managers and single doctypes
			} else {
				var route;
				if(dataent.boot.treeviews.indexOf(breadcrumbs.doctype) !== -1) {
					var view = dataent.model.user_settings[breadcrumbs.doctype].last_view || 'Tree';
					route = view + '/' + breadcrumbs.doctype;
				} else {
					route = 'List/' + breadcrumbs.doctype;
				}
				$(repl('<li><a href="#%(route)s">%(label)s</a></li>',
					{route: route, label: __(breadcrumbs.doctype)}))
					.appendTo($breadcrumbs);
			}
		}

		$("body").removeClass("no-breadcrumbs");
	},

	rename: function(doctype, old_name, new_name) {
		var old_route_str = ["Form", doctype, old_name].join("/");
		var new_route_str = ["Form", doctype, new_name].join("/");
		dataent.breadcrumbs.all[new_route_str] = dataent.breadcrumbs.all[old_route_str];
		delete dataent.breadcrumbs.all[old_route_str];
	}

}

