QUnit.module('form');

QUnit.test("Test Linked With", function(assert) {
	assert.expect(2);
	const done = assert.async();

	dataent.run_serially([
		() => dataent.set_route('Form', 'Module Def', 'Contacts'),
		() => dataent.tests.click_page_head_item('Menu'),
		() => dataent.tests.click_dropdown_item('Links'),
		() => dataent.timeout(4),
		() => {
			assert.equal(cur_dialog.title, 'Linked With', 'Linked with dialog is opened');
			const link_tables_count = cur_dialog.$wrapper.find('.list-item-table').length;
			assert.equal(link_tables_count, 2, 'Two DocTypes are linked with Contacts');
		},
		done
	]);
});