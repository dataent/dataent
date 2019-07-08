QUnit.module('views');

QUnit.test("Test: Kanban view", function(assert) {
	assert.expect(4);
	let done = assert.async();

	dataent.run_serially([
		() => dataent.set_route("List", "ToDo", "List"),
		// calculate number of element in list
		() => dataent.timeout(1),
		() => dataent.set_route("List", "ToDo", "Kanban", "Kanban test"),
		() => dataent.timeout(2),
		() => {
			assert.equal('Kanban', cur_list.view_name,
				"Current view is kanban.");
			assert.equal("Kanban test", cur_list.page_title,
				"Kanban view opened successfully.");
			// check if all elements are visible in kanban view
			const $high_priority_cards =
				$('.kanban-column[data-column-value="High"] .kanban-card-wrapper');
			const $low_priority_cards =
				$('.kanban-column[data-column-value="Low"] .kanban-card-wrapper');

			assert.equal($high_priority_cards.length, 1);
			assert.equal($low_priority_cards.length, 1);
		},
		() => done()
	]);
});