// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt
/* eslint-disable no-console */

function $c(command, args, callback, error, no_spinner, freeze_msg, btn) {
	console.warn("This function '$c' has been deprecated and will be removed soon.");
	return dataent.request.call({
		type: "POST",
		args: $.extend(args, {cmd: command}),
		success: callback,
		error: error,
		btn: btn,
		freeze: freeze_msg,
		show_spinner: !no_spinner
	});
}

// For calling an object
function $c_obj(doc, method, arg, callback, no_spinner, freeze_msg, btn) {
	console.warn("This function '$c_obj' has been deprecated and will be removed soon.");

	if(arg && typeof arg!='string') arg = JSON.stringify(arg);

	var args = {
		cmd:'runserverobj',
		args: arg,
		method: method
	};

	if(typeof doc=='string') {
		args.doctype = doc;
	} else {
		args.docs = doc;
	}

	return dataent.request.call({
		type: "POST",
		args: args,
		success: callback,
		btn: btn,
		freeze: freeze_msg,
		show_spinner: !no_spinner
	});
}

// For calling an for output as csv
function $c_obj_csv(doc, method, arg) {
	console.warn("This function '$c_obj_csv' has been deprecated and will be removed soon.");
	// single

	var args = {};
	args.cmd = 'runserverobj';
	args.as_csv = 1;
	args.method = method;
	args.arg = arg;

	if(doc.substr)
		args.doctype = doc;
	else
		args.docs = doc;

	// open
	open_url_post(dataent.request.url, args);
}

window.open_url_post = function open_url_post(URL, PARAMS, new_window) {
	if (window.cordova) {
		let url = URL + 'api/method/' + PARAMS.cmd + dataent.utils.make_query_string(PARAMS, false);
		window.location.href = url;
	} else {
		// call a url as POST
		_open_url_post(URL, PARAMS, new_window);
	}
};

function _open_url_post(URL, PARAMS, new_window) {
	var temp=document.createElement("form");
	temp.action=URL;
	temp.method="POST";
	temp.style.display="none";
	if(new_window){
		temp.target = '_blank';
	}
	PARAMS["csrf_token"] = dataent.csrf_token;
	for(var x in PARAMS) {
		var opt=document.createElement("textarea");
		opt.name=x;
		var val = PARAMS[x];
		if(typeof val!='string')
			val = JSON.stringify(val);
		opt.value=val;
		temp.appendChild(opt);
	}
	document.body.appendChild(temp);
	temp.submit();
	return temp;
}

Object.assign(window, {
	$c, $c_obj, $c_obj_csv
});