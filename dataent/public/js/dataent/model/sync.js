// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

$.extend(dataent.model, {
	docinfo: {},
	sync: function(r) {
		/* docs:
			extract docs, docinfo (attachments, comments, assignments)
			from incoming request and set in `locals` and `dataent.model.docinfo`
		*/
		var isPlain;
		if(!r.docs && !r.docinfo) r = {docs:r};

		isPlain = $.isPlainObject(r.docs);
		if(isPlain) r.docs = [r.docs];

		if(r.docs) {

			for(var i=0, l=r.docs.length; i<l; i++) {
				var d = r.docs[i];

				if (locals[d.doctype] && locals[d.doctype][d.name]) {
					// update values
					dataent.model.update_in_locals(d);
				} else {
					dataent.model.add_to_locals(d);
				}

				d.__last_sync_on = new Date();

				if(d.doctype==="DocType") {
					dataent.meta.sync(d);
				}

				if(d.localname) {
					dataent.model.new_names[d.localname] = d.name;
					$(document).trigger('rename', [d.doctype, d.localname, d.name]);
					delete locals[d.doctype][d.localname];

					// update docinfo to new dict keys
					if(i===0) {
						dataent.model.docinfo[d.doctype][d.name] = dataent.model.docinfo[d.doctype][d.localname];
						dataent.model.docinfo[d.doctype][d.localname] = undefined;
					}
				}
			}



		}

		// set docinfo (comments, assign, attachments)
		if(r.docinfo) {
			var doc;
			if(r.docs) {
				doc = r.docs[0];
			} else {
				if(cur_frm) doc = cur_frm.doc;
			}
			if(doc) {
				if(!dataent.model.docinfo[doc.doctype])
					dataent.model.docinfo[doc.doctype] = {};
				dataent.model.docinfo[doc.doctype][doc.name] = r.docinfo;
			}
		}

		return r.docs;
	},
	add_to_locals: function(doc) {
		if(!locals[doc.doctype])
			locals[doc.doctype] = {};

		if(!doc.name && doc.__islocal) { // get name (local if required)
			if(!doc.parentfield) dataent.model.clear_doc(doc);

			doc.name = dataent.model.get_new_name(doc.doctype);

			if(!doc.parentfield) dataent.provide("dataent.model.docinfo." + doc.doctype + "." + doc.name);
		}

		locals[doc.doctype][doc.name] = doc;

		// add child docs to locals
		if(!doc.parentfield) {
			for(var i in doc) {
				var value = doc[i];

				if($.isArray(value)) {
					for (var x=0, y=value.length; x < y; x++) {
						var d = value[x];

						if(typeof d=='object' && !d.parent)
							d.parent = doc.name;

						dataent.model.add_to_locals(d);
					}
				}
			}
		}
	},
	update_in_locals: function(doc) {
		// update values in the existing local doc instead of replacing
		let local_doc = locals[doc.doctype][doc.name];
		let clear_keys = function(source, target) {
			Object.keys(target).map(key => {
				if (source[key] == undefined) delete target[key];
			});
		}
		
		for (let fieldname in doc) {
			let df = dataent.meta.get_field(doc.doctype, fieldname);
			if (df && df.fieldtype === 'Table') {
				// table
				if (!(doc[fieldname] instanceof Array)) {
					doc[fieldname] = [];
				}

				if (!(local_doc[fieldname] instanceof Array)) {
					local_doc[fieldname] = [];
				}
				
				// child table, override each row and append new rows if required
				for (let i=0; i < doc[fieldname].length; i++ ) {
					let d = doc[fieldname][i];
					let local_d = local_doc[fieldname][i];
					if (local_d) {
						// deleted and added again
						if (!locals[d.doctype]) locals[d.doctype] = {};

						if (!d.name) {
							// incoming row is new, find a new name
							d.name = dataent.model.get_new_name(doc.doctype);
						}

						// if incoming row is not registered, register it
						if (!locals[d.doctype][d.name]) {
							// detach old key
							delete locals[d.doctype][local_d.name];

							// re-attach with new name
							locals[d.doctype][d.name] = local_d;
						}

						// row exists, just copy the values
						Object.assign(local_d, d);
						clear_keys(d, local_d);
						
					} else {
						local_doc[fieldname].push(d);
						if (!d.parent) d.parent = doc.name;
						dataent.model.add_to_locals(d);
					}
				}

				// remove extra rows
				if (local_doc[fieldname].length > doc[fieldname].length) {
					for (let i = doc[fieldname].length; i < local_doc[fieldname].length; i++) {

						// clear from local
						let d = local_doc[fieldname][i];
						if (locals[d.doctype] && locals[d.doctype][d.name]) {
							delete locals[d.doctype][d.name];
						}
					}
					local_doc[fieldname].length = doc[fieldname].length;

				}
			} else {
				// literal
				local_doc[fieldname] = doc[fieldname];
			}
		}
		
		// clear keys on parent
		clear_keys(doc, local_doc);
	}

});
