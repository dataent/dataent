// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.provide("dataent.help");

dataent.help.youtube_id = {};

dataent.help.has_help = function(doctype) {
	return dataent.help.youtube_id[doctype];
}

dataent.help.show = function(doctype) {
	if(dataent.help.youtube_id[doctype]) {
		dataent.help.show_video(dataent.help.youtube_id[doctype]);
	}
}

dataent.help.show_video = function(youtube_id, title) {
	if($("body").width() > 768) {
		var size = [670, 377];
	} else {
		var size = [560, 315];
	}
	var dialog = dataent.msgprint('<iframe width="'+size[0]+'" height="'+size[1]+'" \
		src="https://www.youtube.com/embed/'+ youtube_id +'" \
		frameborder="0" allowfullscreen></iframe>' + (dataent.help_feedback_link || ""),
	title || __("Help"));

	dialog.$wrapper.addClass("video-modal");
}

$("body").on("click", "a.help-link", function() {
	var doctype = $(this).attr("data-doctype");
	doctype && dataent.help.show(doctype);
});
