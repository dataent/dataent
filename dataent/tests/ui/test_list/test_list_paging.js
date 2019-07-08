QUnit.module('views');

QUnit.test("Test paging in list view", function(assert) {
	assert.expect(5);
	let done = assert.async();

	dataent.run_serially([
		() => dataent.set_route('List', 'DocType'),
		() => dataent.timeout(0.5),
		() => assert.deepEqual(['List', 'DocType', 'List'], dataent.get_route(),
			"List opened successfully."),
		//check elements less then page length [20 in this case]
		() => assert.equal(cur_list.data.length, 20, 'show 20 items'),
		() => dataent.click_button('More'),
		() => dataent.timeout(2),
		() => assert.equal(cur_list.data.length, 40, 'show more items'),
		() => dataent.tests.click_button('100'),
		() => dataent.timeout(2),
		() => assert.ok(cur_list.data.length > 40, 'show 100 items'),
		() => dataent.tests.click_button('20'),
		() => dataent.timeout(2),
		() => assert.equal(cur_list.data.length, 20, 'show 20 items again'),
		() => done()
	]);
});