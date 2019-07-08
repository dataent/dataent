QUnit.module('views');

QUnit.test("Calendar View Tests", function(assert) {
	assert.expect(3);
	let done = assert.async();
	let random_text = dataent.utils.get_random(3);
	let today = dataent.datetime.get_today()+" 16:20:35"; //arbitrary value taken to prevent cases like 12a for 12:00am and 12h to 24h conversion
	let visible_time = () => {
		// Method to return the start-time (hours) of the event visible
		return $('.fc-time').text().split('p')[0]; // 'p' because the arbitrary time is pm
	};
	let event_title_text = () => {
		// Method to return the title of the event visible
		return $('.fc-title:visible').text();
	};

	dataent.run_serially([
		// create 2 events, one private, one public
		() => dataent.tests.make("Event", [
			{subject: random_text + ':Pri'},
			{starts_on: today},
			{event_type: 'Private'}
		]),

		() => dataent.timeout(1),

		() => dataent.tests.make("Event", [
			{subject: random_text + ':Pub'},
			{starts_on: today},
			{event_type: 'Public'}
		]),

		() => dataent.timeout(1),

		// Goto Calendar view
		() => dataent.set_route(["List", "Event", "Calendar"]),

		// clear filter
		() => cur_list.filter_area.remove('event_type'),
		() => dataent.timeout(2),
		// Check if event is created
		() => {
			// Check if the event exists and if its title matches with the one created
			assert.ok(event_title_text().includes(random_text + ':Pri'),
				"Event title verified");
		},

		// check filter
		() => cur_list.filter_area.add('Event', 'event_type', '=', 'Public'),
		() => dataent.timeout(1),
		() => {
			// private event should be hidden
			assert.notOk(event_title_text().includes(random_text + ':Pri'),
				"Event title verified");
		},

		// Delete event
		// Goto Calendar view
		() => dataent.set_route(["List", "Event", "Calendar"]),
		() => dataent.timeout(1),
		// delete event
		() => dataent.click_link(random_text + ':Pub'),
		() => {
			dataent.tests.click_page_head_item('Menu');
			dataent.tests.click_dropdown_item('Delete');
		},
		() => dataent.timeout(0.5),
		() => dataent.click_button('Yes'),
		() => dataent.timeout(2),
		() => dataent.set_route(["List", "Event", "Calendar"]),
		() => dataent.click_button("Refresh"),
		() => dataent.timeout(1),

		// Check if event is deleted
		() => assert.notOk(event_title_text().includes(random_text + ':Pub'),
			"Event deleted"),
		() => done()
	]);
});