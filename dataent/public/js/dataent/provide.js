// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// provide a namespace
if(!window.dataent)
	window.dataent = {};

dataent.provide = function(namespace) {
	// docs: create a namespace //
	var nsl = namespace.split('.');
	var parent = window;
	for(var i=0; i<nsl.length; i++) {
		var n = nsl[i];
		if(!parent[n]) {
			parent[n] = {}
		}
		parent = parent[n];
	}
	return parent;
}

dataent.provide("locals");
dataent.provide("dataent.flags");
dataent.provide("dataent.settings");
dataent.provide("dataent.utils");
dataent.provide("dataent.ui");
dataent.provide("dataent.modules");
dataent.provide("dataent.templates");
dataent.provide("dataent.test_data");
