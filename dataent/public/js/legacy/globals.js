// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.provide('dataent.desk.form');
dataent.provide('dataent.desk.report');
dataent.provide('dataent.utils');
dataent.provide('dataent.model');
dataent.provide('dataent.user');
dataent.provide('dataent.session');
dataent.provide('locals');
dataent.provide('locals.DocType');

// for listviews
dataent.provide("dataent.listview_settings");
dataent.provide("dataent.listview_parent_route");

// setup custom binding for history
dataent.settings.no_history = 1;

// constants
window.NEWLINE = '\n';
window.TAB = 9;
window.UP_ARROW = 38;
window.DOWN_ARROW = 40;

// proxy for user globals defined in desk.js

// Name Spaces
// ============

// form
window._f = {};
window._p = {};
window._r = {};

// API globals
window.frms={};
window.cur_frm=null;
