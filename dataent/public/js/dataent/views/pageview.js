// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.provide('dataent.views.pageview');
dataent.provide("dataent.standard_pages");

dataent.views.pageview = {
	with_page: function(name, callback) {
		if(in_list(Object.keys(dataent.standard_pages), name)) {
			if(!dataent.pages[name]) {
				dataent.standard_pages[name]();
			}
			callback();
			return;
		}

		if((locals.Page && locals.Page[name]) || name==window.page_name) {
			// already loaded
			callback();
		} else if(localStorage["_page:" + name] && dataent.boot.developer_mode!=1) {
			// cached in local storage
			dataent.model.sync(JSON.parse(localStorage["_page:" + name]));
			callback();
		} else {
			// get fresh
			return dataent.call({
				method: 'dataent.desk.desk_page.getpage',
				args: {'name':name },
				callback: function(r) {
					if(!r.docs._dynamic_page) {
						localStorage["_page:" + name] = JSON.stringify(r.docs);
					}
					callback();
				},
				freeze: true,
			});
		}
	},
	show: function(name) {
		if(!name) {
			name = (dataent.boot ? dataent.boot.home_page : window.page_name);
		}
		dataent.model.with_doctype("Page", function() {
			dataent.views.pageview.with_page(name, function(r) {
				if(r && r.exc) {
					if(!r['403'])
						dataent.show_not_found(name);
				} else if(!dataent.pages[name]) {
					new dataent.views.Page(name);
				}
				dataent.container.change_to(name);
			});
		});
	}
};

dataent.views.Page = Class.extend({
	init: function(name) {
		this.name = name;
		var me = this;
		// web home page
		if(name==window.page_name) {
			this.wrapper = document.getElementById('page-' + name);
			this.wrapper.label = document.title || window.page_name;
			this.wrapper.page_name = window.page_name;
			dataent.pages[window.page_name] = this.wrapper;
		} else {
			this.pagedoc = locals.Page[this.name];
			if(!this.pagedoc) {
				dataent.show_not_found(name);
				return;
			}
			this.wrapper = dataent.container.add_page(this.name);
			this.wrapper.label = this.pagedoc.title || this.pagedoc.name;
			this.wrapper.page_name = this.pagedoc.name;

			// set content, script and style
			if(this.pagedoc.content)
				this.wrapper.innerHTML = this.pagedoc.content;
			dataent.dom.eval(this.pagedoc.__script || this.pagedoc.script || '');
			dataent.dom.set_style(this.pagedoc.style || '');
		}

		this.trigger_page_event('on_page_load');

		// set events
		$(this.wrapper).on('show', function() {
			window.cur_frm = null;
			me.trigger_page_event('on_page_show');
			me.trigger_page_event('refresh');
		});
	},
	trigger_page_event: function(eventname) {
		var me = this;
		if(me.wrapper[eventname]) {
			me.wrapper[eventname](me.wrapper);
		}
	}
});

dataent.show_not_found = function(page_name) {
	dataent.show_message_page({
		page_name: page_name,
		message: __("Sorry! I could not find what you were looking for."),
		img: "/assets/dataent/images/ui/bubble-tea-sorry.svg"
	});
};

dataent.show_not_permitted = function(page_name) {
	dataent.show_message_page({
		page_name: page_name,
		message: __("Sorry! You are not permitted to view this page."),
		img: "/assets/dataent/images/ui/bubble-tea-sorry.svg",
		// icon: "octicon octicon-circle-slash"
	});
};

dataent.show_message_page = function(opts) {
	// opts can include `page_name`, `message`, `icon` or `img`
	if(!opts.page_name) {
		opts.page_name = dataent.get_route_str();
	}

	if(opts.icon) {
		opts.img = repl('<span class="%(icon)s message-page-icon"></span> ', opts);
	} else if (opts.img) {
		opts.img = repl('<img src="%(img)s" class="message-page-image">', opts);
	}

	var page = dataent.pages[opts.page_name] || dataent.container.add_page(opts.page_name);
	$(page).html(
		repl('<div class="page message-page">\
			<div class="text-center message-page-content">\
				%(img)s\
				<p class="lead">%(message)s</p>\
				<a class="btn btn-default btn-sm btn-home" href="#">%(home)s</a>\
			</div>\
		</div>', {
				img: opts.img || "",
				message: opts.message || "",
				home: __("Home")
			})
	);

	dataent.container.change_to(opts.page_name);
};
