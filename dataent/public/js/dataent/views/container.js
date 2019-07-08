// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// page container
dataent.provide('dataent.pages');
dataent.provide('dataent.views');

window.cur_page = null;
dataent.views.Container = Class.extend({
	_intro: "Container contains pages inside `#container` and manages \
			page creation, switching",
	init: function() {
		this.container = $('#body_div').get(0);
		this.page = null; // current page
		this.pagewidth = $(this.container).width();
		this.pagemargin = 50;

		var me = this;

		$(document).on("page-change", function() {
			// set data-route in body
			var route_str = dataent.get_route_str();
			$("body").attr("data-route", route_str);
			$("body").attr("data-sidebar", me.has_sidebar() ? 1 : 0);
		});

		$(document).bind('rename', function(event, dt, old_name, new_name) {
			dataent.breadcrumbs.rename(dt, old_name, new_name);
		});
	},
	add_page: function(label) {
		var page = $('<div class="content page-container"></div>')
			.attr('id', "page-" + label)
			.attr("data-page-route", label)
			.hide()
			.appendTo(this.container).get(0);
		page.label = label;
		dataent.pages[label] = page;

		return page;
	},
	change_to: function(label) {
		cur_page = this;
		if(this.page && this.page.label === label) {
			$(this.page).trigger('show');
			return;
		}

		var me = this;
		if(label.tagName) {
			// if sent the div, get the table
			var page = label;
		} else {
			var page = dataent.pages[label];
		}
		if(!page) {
			console.log(__('Page not found')+ ': ' + label);
			return;
		}

		// hide dialog
		if(window.cur_dialog && cur_dialog.display && !cur_dialog.keep_open) {
			cur_dialog.hide();
		}

		// hide current
		if(this.page && this.page != page) {
			$(this.page).hide();
			$(this.page).trigger('hide');
		}

		// show new
		if(!this.page || this.page != page) {
			this.page = page;
			// $(this.page).fadeIn(300);
			$(this.page).show();
		}

		$(document).trigger("page-change");

		this.page._route = window.location.hash;
		$(this.page).trigger('show');
		dataent.utils.scroll_to(0);
		dataent.breadcrumbs.update();

		return this.page;
	},
	has_sidebar: function() {
		var flag = 0;
		var route_str = dataent.get_route_str();
		// check in dataent.ui.pages
		flag = dataent.ui.pages[route_str] && !dataent.ui.pages[route_str].single_column;

		// sometimes dataent.ui.pages is updated later,
		// so check the dom directly
		if(!flag) {
			var page_route = route_str.split('/').slice(0, 2).join('/');
			flag = $(`.page-container[data-page-route="${page_route}"] .layout-side-section`).length ? 1 : 0;
		}

		return flag;
	},
});


