QUnit.module('Setup');

QUnit.test("Test List Count", function(assert) {
	assert.expect(3);
	const done = assert.async();

	dataent.run_serially([
		() => dataent.set_route('List', 'DocType'),
		() => dataent.timeout(0.5),
		() => {
			let count = $('.list-count').text().split(' ')[0];
			assert.equal(cur_list.data.length, count, "Correct Count");
		},

		() => dataent.timeout(1),
		() => cur_list.filter_area.add('Doctype', 'module', '=', 'Desk'),
		() => dataent.click_button('Refresh'),
		() => {
			let count = $('.list-count').text().split(' ')[0];
			assert.equal(cur_list.data.length, count, "Correct Count");
		},

		() => cur_list.filter_area.clear(),
		() => dataent.timeout(1),
		() => {
			cur_list.filter_area.add('DocField', 'fieldname', 'like', 'owner');
			let count = $('.list-count').text().split(' ')[0];
			assert.equal(cur_list.data.length, count, "Correct Count");
		},

		done
	]);
});