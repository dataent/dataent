// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.provide("dataent.workflow");

dataent.workflow = {
	state_fields: {},
	workflows: {},
	setup: function(doctype) {
		var wf = dataent.get_list("Workflow", {document_type: doctype});
		if(wf.length) {
			dataent.workflow.workflows[doctype] = wf[0];
			dataent.workflow.state_fields[doctype] = wf[0].workflow_state_field;
		} else {
			dataent.workflow.state_fields[doctype] = null;
		}
	},
	get_state_fieldname: function(doctype) {
		if(dataent.workflow.state_fields[doctype]===undefined) {
			dataent.workflow.setup(doctype);
		}
		return dataent.workflow.state_fields[doctype];
	},
	get_default_state: function(doctype, docstatus) {
		dataent.workflow.setup(doctype);
		var value = null;
		$.each(dataent.workflow.workflows[doctype].states, function(i, workflow_state) {
			if(cint(workflow_state.doc_status)===cint(docstatus)) {
				value = workflow_state.state;
				return false;
			}
		});
		return value;
	},
	get_transitions: function(doc) {
		dataent.workflow.setup(doc.doctype);
		return dataent.xcall('dataent.model.workflow.get_transitions', {doc: doc});
	},
	get_document_state: function(doctype, state) {
		dataent.workflow.setup(doctype);
		return dataent.get_children(dataent.workflow.workflows[doctype], "states", {state:state})[0];
	},
	is_self_approval_enabled: function(doctype) {
		return dataent.workflow.workflows[doctype].allow_self_approval;
	},
	is_read_only: function(doctype, name) {
		var state_fieldname = dataent.workflow.get_state_fieldname(doctype);
		if(state_fieldname) {
			var doc = locals[doctype][name];
			if(!doc)
				return false;
			if(doc.__islocal)
				return false;

			var state = doc[state_fieldname] ||
				dataent.workflow.get_default_state(doctype, doc.docstatus);

			var allow_edit = state ? dataent.workflow.get_document_state(doctype, state) && dataent.workflow.get_document_state(doctype, state).allow_edit : null;

			if(!dataent.user_roles.includes(allow_edit)) {
				return true;
			}
		}
		return false;
	},
	get_update_fields: function(doctype) {
		var update_fields = $.unique($.map(dataent.workflow.workflows[doctype].states || [],
			function(d) {
				return d.update_field;
			}));
		return update_fields;
	}
};
