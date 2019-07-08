// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// for translation
dataent._messages = {};
dataent._ = function(txt, replace) {
	if(!txt)
		return txt;
	if(typeof(txt) != "string")
		return txt;
	var ret = dataent._messages[txt.replace(/\n/g, "")] || txt;
	if(replace && typeof(replace) === "object") {
		ret = $.format(ret, replace);
	}
	return ret;
};
window.__ = dataent._

dataent.get_languages = function() {
	if(!dataent.languages) {
		dataent.languages = []
		$.each(dataent.boot.lang_dict, function(lang, value){
			dataent.languages.push({'label': lang, 'value': value})
		});
		dataent.languages = dataent.languages.sort(function(a, b) { return (a.value < b.value) ? -1 : 1 });
	}
	return dataent.languages;
};
