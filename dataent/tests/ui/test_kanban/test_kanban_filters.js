QUnit.module('views');

QUnit.test("Test: Filters [Kanban view]", function(assert) {
	assert.expect(3);
	let done = assert.async();

	dataent.run_serially([
		() => dataent.set_route("List", "ToDo", "Kanban", "Kanban test"),
		() => dataent.timeout(1),
		() => {
			assert.deepEqual(["List", "ToDo", "Kanban", "Kanban test"], dataent.get_route(),
				"Kanban view opened successfully.");
		},
		// set filter values
		() => cur_list.filter_area.add('ToDo', 'priority', '=', 'Low'),
		() => dataent.timeout(1),
		() => cur_list.page.btn_secondary.click(),
		() => dataent.timeout(1),
		() => {
			assert.equal(cur_list.data[0].priority, 'Low',
				'visible element has low priority');
			let non_low_items = cur_list.data.filter(d => d.priority != 'Low');
			assert.equal(non_low_items.length, 0, 'No item without low priority');
		},
		() => done()
	]);
});