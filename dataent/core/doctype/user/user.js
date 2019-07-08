dataent.ui.form.on('User', {
	before_load: function(frm) {
		var update_tz_select = function(user_language) {
			frm.set_df_property("time_zone", "options", [""].concat(dataent.all_timezones));
		}

		if(!dataent.all_timezones) {
			dataent.call({
				method: "dataent.core.doctype.user.user.get_timezones",
				callback: function(r) {
					dataent.all_timezones = r.message.timezones;
					update_tz_select();
				}
			});
		} else {
			update_tz_select();
		}

	},

	role_profile_name: function(frm) {
		if(frm.doc.role_profile_name) {
			dataent.call({
				"method": "dataent.core.doctype.user.user.get_role_profile",
				args: {
					role_profile: frm.doc.role_profile_name
				},
				callback: function (data) {
					frm.set_value("roles", []);
					$.each(data.message || [], function(i, v){
						var d = frm.add_child("roles");
						d.role = v.role;
					});
					frm.roles_editor.show();
				}
			});
		}
	},

	onload: function(frm) {
		frm.can_edit_roles = has_access_to_edit_user();

		if(frm.can_edit_roles && !frm.is_new()) {
			if(!frm.roles_editor) {
				var role_area = $('<div style="min-height: 300px">')
					.appendTo(frm.fields_dict.roles_html.wrapper);
				frm.roles_editor = new dataent.RoleEditor(role_area, frm, frm.doc.role_profile_name ? 1 : 0);

				var module_area = $('<div style="min-height: 300px">')
					.appendTo(frm.fields_dict.modules_html.wrapper);
				frm.module_editor = new dataent.ModuleEditor(frm, module_area);
			} else {
				frm.roles_editor.show();
			}
		}
	},
	refresh: function(frm) {
		var doc = frm.doc;
		if(!frm.is_new() && !frm.roles_editor && frm.can_edit_roles) {
			frm.reload_doc();
			return;
		}
		if(doc.name===dataent.session.user && !doc.__unsaved
			&& dataent.all_timezones
			&& (doc.language || dataent.boot.user.language)
			&& doc.language !== dataent.boot.user.language) {
			dataent.msgprint(__("Refreshing..."));
			window.location.reload();
		}

		frm.toggle_display(['sb1', 'sb3', 'modules_access'], false);

		if(!frm.is_new()) {
			frm.add_custom_button(__("Set Desktop Icons"), function() {
				dataent.dataent_toolbar.modules_select.show(doc.name);
			}, null, "btn-default")

			if(has_access_to_edit_user()) {

				frm.add_custom_button(__("Set User Permissions"), function() {
					dataent.route_options = {
						"user": doc.name
					};
					dataent.set_route('List', 'User Permission');
				}, __("Permissions"))

				frm.add_custom_button(__('View Permitted Documents'),
					() => dataent.set_route('query-report', 'Permitted Documents For User',
						{user: frm.doc.name}), __("Permissions"));

				frm.toggle_display(['sb1', 'sb3', 'modules_access'], true);
			}

			frm.add_custom_button(__("Reset Password"), function() {
				dataent.call({
					method: "dataent.core.doctype.user.user.reset_password",
					args: {
						"user": frm.doc.name
					}
				})
			}, __("Password"));

			frm.add_custom_button(__("Reset OTP Secret"), function() {
				dataent.call({
					method: "dataent.core.doctype.user.user.reset_otp_secret",
					args: {
						"user": frm.doc.name
					}
				})
			}, __("Password"));

			frm.trigger('enabled');

			if (frm.roles_editor && frm.can_edit_roles) {
				frm.roles_editor.disable = frm.doc.role_profile_name ? 1 : 0;
				frm.roles_editor.show();
			}

			frm.module_editor && frm.module_editor.refresh();

			if(dataent.session.user==doc.name) {
				// update display settings
				if(doc.user_image) {
					dataent.boot.user_info[dataent.session.user].image = dataent.utils.get_file_link(doc.user_image);
				}
			}
		}
		if (frm.doc.user_emails){
			var found =0;
			for (var i = 0;i<frm.doc.user_emails.length;i++){
				if (frm.doc.email==frm.doc.user_emails[i].email_id){
					found = 1;
				}
			}
			if (!found){
				frm.add_custom_button(__("Create User Email"), function() {
					frm.events.create_user_email(frm)
				})
			}
		}

		if (dataent.route_flags.unsaved===1){
			delete dataent.route_flags.unsaved;
			for ( var i=0;i<frm.doc.user_emails.length;i++) {
				frm.doc.user_emails[i].idx=frm.doc.user_emails[i].idx+1;
			}
			cur_frm.dirty();
		}

	},
	validate: function(frm) {
		if(frm.roles_editor) {
			frm.roles_editor.set_roles_in_table()
		}
	},
	enabled: function(frm) {
		var doc = frm.doc;
		if(!frm.is_new() && has_access_to_edit_user()) {
			frm.toggle_display(['sb1', 'sb3', 'modules_access'], doc.enabled);
			frm.set_df_property('enabled', 'read_only', 0);
		}

		if(dataent.session.user!=="Administrator") {
			frm.toggle_enable('email', frm.is_new());
		}
	},
	create_user_email:function(frm) {
		dataent.call({
			method: 'dataent.core.doctype.user.user.has_email_account',
			args: {
				email: frm.doc.email
			},
			callback: function(r) {
				if (r.message == undefined) {
					dataent.route_options = {
						"email_id": frm.doc.email,
						"awaiting_password": 1,
						"enable_incoming": 1
					};
					dataent.model.with_doctype("Email Account", function (doc) {
						var doc = dataent.model.get_new_doc("Email Account");
						dataent.route_flags.linked_user = frm.doc.name;
						dataent.route_flags.delete_user_from_locals = true;
						dataent.set_route("Form", "Email Account", doc.name);
					})
				} else {
					dataent.route_flags.create_user_account = frm.doc.name;
					dataent.set_route("Form", "Email Account", r.message[0]["name"]);
				}
			}
		})
	},
	generate_keys: function(frm){
		dataent.call({
			method: 'dataent.core.doctype.user.user.generate_keys',
			args: {
				user: frm.doc.name
			},
			callback: function(r){
				if(r.message){
					dataent.msgprint(__("Save API Secret: ") + r.message.api_secret);
				}
			}
		})
	}
})

function has_access_to_edit_user() {
	return has_common(dataent.user_roles, get_roles_for_editing_user());
}

function get_roles_for_editing_user() {
	return dataent.get_meta('User').permissions
		.filter(perm => perm.permlevel >= 1 && perm.write)
		.map(perm => perm.role) || ['System Manager'];
}

dataent.ModuleEditor = Class.extend({
	init: function(frm, wrapper) {
		this.wrapper = $('<div class="row module-block-list"></div>').appendTo(wrapper);
		this.frm = frm;
		this.make();
	},
	make: function() {
		var me = this;
		this.frm.doc.__onload.all_modules.forEach(function(m) {
			$(repl('<div class="col-sm-6"><div class="checkbox">\
				<label><input type="checkbox" class="block-module-check" data-module="%(module)s">\
				%(module)s</label></div></div>', {module: m})).appendTo(me.wrapper);
		});
		this.bind();
	},
	refresh: function() {
		var me = this;
		this.wrapper.find(".block-module-check").prop("checked", true);
		$.each(this.frm.doc.block_modules, function(i, d) {
			me.wrapper.find(".block-module-check[data-module='"+ d.module +"']").prop("checked", false);
		});
	},
	bind: function() {
		var me = this;
		this.wrapper.on("change", ".block-module-check", function() {
			var module = $(this).attr('data-module');
			if($(this).prop("checked")) {
				// remove from block_modules
				me.frm.doc.block_modules = $.map(me.frm.doc.block_modules || [], function(d) { if(d.module != module){ return d } });
			} else {
				me.frm.add_child("block_modules", {"module": module});
			}
		});
	}
})
