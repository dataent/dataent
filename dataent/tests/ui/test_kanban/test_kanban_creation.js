QUnit.module('views');

QUnit.test("Test: Creation [Kanban view]", function(assert) {
	assert.expect(2);
	let done = assert.async();

	const board_name = 'Kanban test';

	dataent.run_serially([
		() => dataent.set_route("List", "ToDo", "List"),
		// wait for cur_list to initialize
		() => cur_list.init(),
		// click kanban in side bar
		() => dataent.tests.click_link('Kanban'),
		() => dataent.tests.click_link('New Kanban Board'),
		() => dataent.timeout(0.5),
		// create new kanban
		() => {
			assert.equal(cur_dialog.title, 'New Kanban Board',
				"Dialog for new kanban opened.");
			cur_dialog.set_value('board_name', board_name);
			cur_dialog.set_value('field_name', 'Priority');
		},
		() => dataent.timeout(0.5),
		() => cur_dialog.get_primary_btn().click(),
		() => dataent.timeout(1),
		() => dataent.set_route("List", "Kanban Board", "List"),
		() => dataent.timeout(0.5),
		// check in kanban list if new kanban is created
		() => assert.equal(cur_list.data[0].name, board_name,
			"Added kanban is visible in kanban list."),
		() => done()
	]);
});