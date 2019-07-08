dataent.listview_settings['Chat Message'] = {
	filters: [
		['Chat Message', 'user',  '==', dataent.session.user, true]
		// I need an or_filter here.
		// ['Chat Room',    'owner', '==', dataent.session.user, true],
		// ['Chat Room',    dataent.session.user, 'in', 'users', true]
	]
};