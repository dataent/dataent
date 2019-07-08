dataent.listview_settings['Chat Room'] = {
	filters: [
		['Chat Room', 'owner', '=', dataent.session.user, true],
		['Chat Room User', 'user', '=', dataent.session.user, true]
	]
};