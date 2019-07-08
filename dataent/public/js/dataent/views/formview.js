// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.provide('dataent.views.formview');

dataent.views.FormFactory = class FormFactory extends dataent.views.Factory {
	make(route) {
		var me = this,
			dt = route[1];

		if(!dataent.views.formview[dt]) {
			dataent.model.with_doctype(dt, function() {
				me.page = dataent.container.add_page("Form/" + dt);
				dataent.views.formview[dt] = me.page;
				me.page.frm = new _f.Frm(dt, me.page, true);
				me.show_doc(route);
			});
		} else {
			me.show_doc(route);
		}


		if(!this.initialized) {
			$(document).on("page-change", function() {
				dataent.ui.form.close_grid_form();
			});

			dataent.realtime.on("new_communication", function(data) {
				dataent.timeline.new_communication(data);
			});

			dataent.realtime.on("delete_communication", function(data) {
				dataent.timeline.delete_communication(data);
			});

			dataent.realtime.on('update_communication', function(data) {
				dataent.timeline.update_communication(data);
			});

			dataent.realtime.on("doc_viewers", function(data) {
				dataent.ui.form.set_viewers(data);
			});
		}


		this.initialized = true;
	}

	show_doc(route) {
		var dt = route[1],
			dn = route.slice(2).join("/"),
			me = this;

		if(dataent.model.new_names[dn]) {
			dn = dataent.model.new_names[dn];
			dataent.set_route("Form", dt, dn);
			return;
		}

		dataent.model.with_doc(dt, dn, function(dn, r) {
			if(r && r['403']) return; // not permitted

			if(!(locals[dt] && locals[dt][dn])) {
				// doc not found, but starts with New,
				// make a new doc and set it
				var new_str = __("New") + " ";
				if(dn && dn.substr(0, new_str.length)==new_str) {
					var new_name = dataent.model.make_new_doc_and_get_name(dt, true);
					if(new_name===dn) {
						me.load(dt, dn);
					} else {
						dataent.set_route("Form", dt, new_name)
					}
				} else {
					dataent.show_not_found(route);
				}
				return;
			}
			me.load(dt, dn);
		});
	}

	load(dt, dn) {
		dataent.container.change_to("Form/" + dt);
		dataent.views.formview[dt].frm.refresh(dn);
	}
}
