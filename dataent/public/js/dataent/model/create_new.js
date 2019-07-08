// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.provide("dataent.model");

$.extend(dataent.model, {
	new_names: {},
	new_name_count: {},

	get_new_doc: function(doctype, parent_doc, parentfield, with_mandatory_children) {
		dataent.provide("locals." + doctype);
		var doc = {
			docstatus: 0,
			doctype: doctype,
			name: dataent.model.get_new_name(doctype),
			__islocal: 1,
			__unsaved: 1,
			owner: dataent.session.user
		};
		dataent.model.set_default_values(doc, parent_doc);

		if(parent_doc) {
			$.extend(doc, {
				parent: parent_doc.name,
				parentfield: parentfield,
				parenttype: parent_doc.doctype,
			});
			if(!parent_doc[parentfield]) parent_doc[parentfield] = [];
			doc.idx = parent_doc[parentfield].length + 1;
			parent_doc[parentfield].push(doc);
		} else {
			dataent.provide("dataent.model.docinfo." + doctype + "." + doc.name);
		}

		dataent.model.add_to_locals(doc);

		if(with_mandatory_children) {
			dataent.model.create_mandatory_children(doc);
		}

		if (!parent_doc) {
			doc.__run_link_triggers = 1;
		}

		// set the name if called from a link field
		if(dataent.route_options && dataent.route_options.name_field) {

			var meta = dataent.get_meta(doctype);
			// set title field / name as name
			if(meta.autoname && meta.autoname.indexOf("field:")!==-1) {
				doc[meta.autoname.substr(6)] = dataent.route_options.name_field;
			} else if(meta.title_field) {
				doc[meta.title_field] = dataent.route_options.name_field;
			}


			delete dataent.route_options.name_field;
		}

		// set route options
		if(dataent.route_options && !doc.parent) {
			$.each(dataent.route_options, function(fieldname, value) {
				var df = dataent.meta.has_field(doctype, fieldname);
				if(df && in_list(['Link', 'Data', 'Select', 'Dynamic Link'], df.fieldtype) && !df.no_copy) {
					doc[fieldname]=value;
				}
			});
			dataent.route_options = null;
		}

		return doc;
	},

	make_new_doc_and_get_name: function(doctype, with_mandatory_children) {
		return dataent.model.get_new_doc(doctype, null, null, with_mandatory_children).name;
	},

	get_new_name: function(doctype) {
		var cnt = dataent.model.new_name_count
		if(!cnt[doctype])
			cnt[doctype] = 0;
		cnt[doctype]++;
		return __('New') + ' '+ __(doctype) + ' ' + cnt[doctype];
	},

	set_default_values: function(doc, parent_doc) {
		var doctype = doc.doctype;
		var docfields = dataent.meta.docfield_list[doctype] || [];
		var updated = [];
		for(var fid=0;fid<docfields.length;fid++) {
			var f = docfields[fid];
			if(!in_list(dataent.model.no_value_type, f.fieldtype) && doc[f.fieldname]==null) {
				var v = dataent.model.get_default_value(f, doc, parent_doc);
				if(v) {
					if(in_list(["Int", "Check"], f.fieldtype))
						v = cint(v);
					else if(in_list(["Currency", "Float"], f.fieldtype))
						v = flt(v);

					doc[f.fieldname] = v;
					updated.push(f.fieldname);
				} else if(f.fieldtype == "Select" && f.options && typeof f.options === 'string'
					&& !in_list(["[Select]", "Loading..."], f.options)) {

					doc[f.fieldname] = f.options.split("\n")[0];
				}
			}
		}
		return updated;
	},

	create_mandatory_children: function(doc) {
		var meta = dataent.get_meta(doc.doctype);
		if(meta && meta.istable) return;

		// create empty rows for mandatory table fields
		dataent.meta.docfield_list[doc.doctype].forEach(function(df) {
			if(df.fieldtype==='Table' && df.reqd) {
				dataent.model.add_child(doc, df.fieldname);
			}
		});
	},

	get_default_value: function(df, doc, parent_doc) {
		var user_default = "";
		var user_permissions = dataent.defaults.get_user_permissions();
		let allowed_records = [];
		if(user_permissions) {
			allowed_records = dataent.perm.get_allowed_docs_for_doctype(user_permissions[df.options], doc.doctype);
		}
		var meta = dataent.get_meta(doc.doctype);
		var has_user_permissions = (df.fieldtype==="Link"
			&& !$.isEmptyObject(user_permissions)
			&& df.ignore_user_permissions != 1
			&& allowed_records.length);

		// don't set defaults for "User" link field using User Permissions!
		if (df.fieldtype==="Link" && df.options!=="User") {
			// 1 - look in user permissions for document_type=="Setup".
			// We don't want to include permissions of transactions to be used for defaults.
			if (df.linked_document_type==="Setup"
				&& has_user_permissions && allowed_records.length===1) {
				return allowed_records[0];
			}

			if(!df.ignore_user_permissions) {
				// 2 - look in user defaults
				var user_defaults = dataent.defaults.get_user_defaults(df.options);
				if (user_defaults && user_defaults.length===1) {
					// Use User Permission value when only when it has a single value
					user_default = user_defaults[0];
				}
			}

			if (!user_default) {
				user_default = dataent.defaults.get_user_default(df.fieldname);
			}

			if(!user_default && df.remember_last_selected_value && dataent.boot.user.last_selected_values) {
				user_default = dataent.boot.user.last_selected_values[df.options];
			}

			var is_allowed_user_default = user_default &&
				(!has_user_permissions || allowed_records.includes(user_default));

			// is this user default also allowed as per user permissions?
			if (is_allowed_user_default) {
				return user_default;
			}
		}

		// 3 - look in default of docfield
		if (df['default']) {

			if (df["default"] == "__user" || df["default"].toLowerCase() == "user") {
				return dataent.session.user;

			} else if (df["default"] == "user_fullname") {
				return dataent.session.user_fullname;

			} else if (df["default"] == "Today") {
				return dataent.datetime.get_today();

			} else if ((df["default"] || "").toLowerCase() === "now") {
				return dataent.datetime.now_datetime();

			} else if (df["default"][0]===":") {
				var boot_doc = dataent.model.get_default_from_boot_docs(df, doc, parent_doc);
				var is_allowed_boot_doc = !has_user_permissions || allowed_records.includes(boot_doc);

				if (is_allowed_boot_doc) {
					return boot_doc;
				}
			} else if (df.fieldname===meta.title_field) {
				// ignore defaults for title field
				return "";
			}

			// is this default value is also allowed as per user permissions?
			var is_allowed_default = !has_user_permissions || allowed_records.includes(df.default);
			if (df.fieldtype!=="Link" || df.options==="User" || is_allowed_default) {
				return df["default"];
			}

		} else if (df.fieldtype=="Time") {
			return dataent.datetime.now_time();
		}
	},

	get_default_from_boot_docs: function(df, doc, parent_doc) {
		// set default from partial docs passed during boot like ":User"
		if(dataent.get_list(df["default"]).length > 0) {
			var ref_fieldname = df["default"].slice(1).toLowerCase().replace(" ", "_");
			var ref_value = parent_doc ?
				parent_doc[ref_fieldname] :
				dataent.defaults.get_user_default(ref_fieldname);
			var ref_doc = ref_value ? dataent.get_doc(df["default"], ref_value) : null;

			if(ref_doc && ref_doc[df.fieldname]) {
				return ref_doc[df.fieldname];
			}
		}
	},

	add_child: function(parent_doc, doctype, parentfield, idx) {
		// if given doc, fieldname only
		if(arguments.length===2) {
			parentfield = doctype;
			doctype = dataent.meta.get_field(parent_doc.doctype, parentfield).options;
		}

		// create row doc
		idx = idx ? idx - 0.1 : (parent_doc[parentfield] || []).length + 1;

		var child = dataent.model.get_new_doc(doctype, parent_doc, parentfield);
		child.idx = idx;

		// renum for fraction
		if(idx !== cint(idx)) {
			var sorted = parent_doc[parentfield].sort(function(a, b) { return a.idx - b.idx; });
			for(var i=0, j=sorted.length; i<j; i++) {
				var d = sorted[i];
				d.idx = i + 1;
			}
		}

		if (cur_frm && cur_frm.doc == parent_doc) cur_frm.dirty();

		return child;
	},

	copy_doc: function(doc, from_amend, parent_doc, parentfield) {
		var no_copy_list = ['name','amended_from','amendment_date','cancel_reason'];
		var newdoc = dataent.model.get_new_doc(doc.doctype, parent_doc, parentfield);

		for(var key in doc) {
			// dont copy name and blank fields
			var df = dataent.meta.get_docfield(doc.doctype, key);

			if (df && key.substr(0, 2) != '__'
				&& !in_list(no_copy_list, key)
				&& !(df && (!from_amend && cint(df.no_copy) == 1))) {

				var value = doc[key] || [];
				if (df.fieldtype === "Table") {
					for (var i = 0, j = value.length; i < j; i++) {
						var d = value[i];
						dataent.model.copy_doc(d, from_amend, newdoc, df.fieldname);
					}
				} else {
					newdoc[key] = doc[key];
				}
			}
		}

		var user = dataent.session.user;

		newdoc.__islocal = 1;
		newdoc.docstatus = 0;
		newdoc.owner = user;
		newdoc.creation = '';
		newdoc.modified_by = user;
		newdoc.modified = '';

		return newdoc;
	},

	open_mapped_doc: function(opts) {
		if (opts.frm && opts.frm.doc.__unsaved) {
			dataent.throw(__("You have unsaved changes in this form. Please save before you continue."));

		} else if (!opts.source_name && opts.frm) {
			opts.source_name = opts.frm.doc.name;

		// Allow opening a mapped doc without a source document name
		} else if (!opts.frm) {
			opts.source_name = null;
		}

		return dataent.call({
			type: "POST",
			method: 'dataent.model.mapper.make_mapped_doc',
			args: {
				method: opts.method,
				source_name: opts.source_name,
				args: opts.args || null,
				selected_children: opts.frm ? opts.frm.get_selected() : null
			},
			freeze: true,
			callback: function(r) {
				if(!r.exc) {
					dataent.model.sync(r.message);
					if(opts.run_link_triggers) {
						dataent.get_doc(r.message.doctype, r.message.name).__run_link_triggers = true;
					}
					dataent.set_route("Form", r.message.doctype, r.message.name);
				}
			}
		})
	}
});

dataent.create_routes = {};
dataent.new_doc = function (doctype, opts, init_callback) {
	return new Promise(resolve => {
		if(opts && $.isPlainObject(opts)) {
			dataent.route_options = opts;
		}
		dataent.model.with_doctype(doctype, function() {
			if(dataent.create_routes[doctype]) {
				dataent.set_route(dataent.create_routes[doctype])
					.then(() => resolve());
			} else {
				dataent.ui.form.make_quick_entry(doctype, null, init_callback)
					.then(() => resolve());
			}
		});

	});
}
