dataent.provide("dataent.ui.form");

dataent.ui.form.Viewers = Class.extend({
	init: function(opts) {
		$.extend(this, opts);
	},
	get_viewers: function() {
		let docinfo = this.frm.get_docinfo();
		if (docinfo) {
			return docinfo.viewers || {};
		} else {
			return {};
		}
	},
	refresh: function(data_updated) {
		this.parent.empty();

		var viewers = this.get_viewers();

		var users = [];
		var new_users = [];
		for (var i=0, l=(viewers.current || []).length; i < l; i++) {
			var username = viewers.current[i];
			if (username===dataent.session.user) {
				// current user
				continue;
			}

			var user_info = dataent.user_info(username);
			users.push({
				image: user_info.image,
				fullname: user_info.fullname,
				abbr: user_info.abbr,
				color: user_info.color,
				title: __("{0} is currently viewing this document", [user_info.fullname])
			});

			if (viewers.new.indexOf(username)!==-1) {
				new_users.push(user_info.fullname);
			}
		}

		if (users.length) {
			this.parent.parent().removeClass("hidden");
			this.parent.append(dataent.render_template("users_in_sidebar", {"users": users}));
		} else {
			this.parent.parent().addClass("hidden");
		}

		if (data_updated && new_users.length) {
			// new user viewing this document, who wasn't viewing in the past
			if (new_users.length===1) {
				dataent.show_alert(__("{0} is currently viewing this document", [new_users[0]]));
			} else {
				dataent.show_alert(__("{0} are currently viewing this document", [dataent.utils.comma_and(new_users)]));
			}

		}
	}
});

dataent.ui.form.set_viewers = function(data) {
	var doctype = data.doctype;
	var docname = data.docname;
	var docinfo = dataent.model.get_docinfo(doctype, docname);
	var past_viewers = ((docinfo && docinfo.viewers) || {}).past || [];
	var viewers = data.viewers || [];

	var new_viewers = viewers.filter(viewer => !past_viewers.includes(viewer));

	dataent.model.set_docinfo(doctype, docname, "viewers", {
		past: past_viewers.concat(new_viewers),
		new: new_viewers,
		current: viewers
	});

	if (cur_frm && cur_frm.doc && cur_frm.doc.doctype===doctype && cur_frm.doc.name==docname) {
		cur_frm.viewers.refresh(true);
	}
}
