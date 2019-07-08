// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.provide('dataent.pages');
dataent.provide('dataent.views');

dataent.views.Factory = class Factory {
	constructor(opts) {
		$.extend(this, opts);
	}

	show() {
		var page_name = dataent.get_route_str(),
			me = this;

		if(dataent.pages[page_name] && !page_name.includes("Form/")) {
			dataent.container.change_to(page_name);
			if(me.on_show) {
				me.on_show();
			}
		} else {
			var route = dataent.get_route();
			if(route[1]) {
				me.make(route);
			} else {
				dataent.show_not_found(route);
			}
		}
	}

	make_page(double_column, page_name) {
		return dataent.make_page(double_column, page_name);
	}
}

dataent.make_page = function(double_column, page_name) {
	if(!page_name) {
		var page_name = dataent.get_route_str();
	}
	var page = dataent.container.add_page(page_name);

	dataent.ui.make_app_page({
		parent: page,
		single_column: !double_column
	});
	dataent.container.change_to(page_name);
	return page;
}
