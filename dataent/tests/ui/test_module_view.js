QUnit.module('views');

QUnit.test("Test modules view", function(assert) {
	assert.expect(4);
	let done = assert.async();

	dataent.run_serially([

		//click Document Share Report in Permissions section [Report]
		() => dataent.set_route("modules", "Setup"),
		() => dataent.timeout(0.5),
		() => dataent.click_link('Document Share Report'),
		() => assert.deepEqual(dataent.get_route(), ["List", "DocShare", "Report", "Document Share Report"],
			'document share report'),

		//click Print Setting in Printing section [Form]
		() => dataent.set_route("modules", "Setup"),
		() => dataent.timeout(0.5),
		() => dataent.click_link('Print Settings'),
		() => assert.deepEqual(dataent.get_route(), ["Form", "Print Settings"],
			'print settings'),

		//click Workflow Action in Workflow section [List]
		() => dataent.set_route("modules", "Setup"),
		() => dataent.timeout(0.5),
		() => dataent.click_link('Workflow Action'),
		() => assert.deepEqual(dataent.get_route(), ["List", "Workflow Action", "List"],
			'workflow action'),

		//click Workflow Action in Workflow section [List]
		() => dataent.set_route("modules"),
		() => dataent.timeout(0.5),
		() => dataent.click_link('Tools'),
		() => dataent.timeout(0.5),
		() => dataent.click_link('To Do'),
		() => assert.deepEqual(dataent.get_route(), ["List", "ToDo", "List"],
			'todo list'),

		() => done()
	]);
});
