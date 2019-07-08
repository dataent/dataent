// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.defaults = {
	get_user_default: function(key) {
		var defaults = dataent.boot.user.defaults;
		var d = defaults[key];
		if(!d && dataent.defaults.is_a_user_permission_key(key))
			d = defaults[dataent.model.scrub(key)];
		if($.isArray(d)) d = d[0];

		if(!dataent.defaults.in_user_permission(key, d)) {
			return;
		}

		return d;
	},
	get_user_defaults: function(key) {
		var defaults = dataent.boot.user.defaults;
		var d = defaults[key];

		if (dataent.defaults.is_a_user_permission_key(key)) {
			if (d && $.isArray(d) && d.length===1) {
				// Use User Permission value when only when it has a single value
				d = d[0];
			} else {
				d = defaults[key] || defaults[dataent.model.scrub(key)];
			}
		}
		if(!$.isArray(d)) d = [d];

		// filter out values which are not permitted to the user
		d.filter(item => {
			if(dataent.defaults.in_user_permission(key, item)) {
				return item;
			}
		});
		return d;
	},
	get_global_default: function(key) {
		var d = dataent.sys_defaults[key];
		if($.isArray(d)) d = d[0];
		return d;
	},
	get_global_defaults: function(key) {
		var d = dataent.sys_defaults[key];
		if(!$.isArray(d)) d = [d];
		return d;
	},
	set_default: function(key, value, callback) {
		if(typeof value!=="string")
			value = JSON.stringify(value);

		dataent.boot.user.defaults[key] = value;
		return dataent.call({
			method: "dataent.client.set_default",
			args: {
				key: key,
				value: value
			},
			callback: callback || function(r) {}
		});
	},
	set_user_default_local: function(key, value) {
		dataent.boot.user.defaults[key] = value;
	},
	get_default: function(key) {
		var defaults = dataent.boot.user.defaults;
		var value = defaults[key];
		if (dataent.defaults.is_a_user_permission_key(key)) {
			if (value && $.isArray(value) && value.length===1) {
				value = value[0];
			} else {
				value = defaults[dataent.model.scrub(key)];
			}
		}

		if(!dataent.defaults.in_user_permission(key, value)) {
			return;
		}

		if(value) {
			try {
				return JSON.parse(value)
			} catch(e) {
				return value;
			}
		}
	},

	is_a_user_permission_key: function(key) {
		return key.indexOf(":")===-1 && key !== dataent.model.scrub(key);
	},

	in_user_permission: function(key, value) {
		let user_permission = this.get_user_permissions()[dataent.model.unscrub(key)];

		if (user_permission && user_permission.length) {

			let doc_found = user_permission.some(perm => {
				return perm.doc === value;
			});
			return doc_found;

		} else {
			// there is no user permission for this doctype
			// so we can allow this doc i.e., value
			return true;
		}

	},

	get_user_permissions: function() {
		return this._user_permissions || {};
	},

	update_user_permissions: function() {
		const method = 'dataent.core.doctype.user_permission.user_permission.get_user_permissions';
		dataent.call(method).then(r => {
			if (r.message) {
				this._user_permissions = Object.assign({}, r.message);
			}
		});
	}
};
