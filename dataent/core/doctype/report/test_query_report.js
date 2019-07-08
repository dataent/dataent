// Test for creating query report
QUnit.test("Test Query Report", function(assert){
	assert.expect(2);
	let done = assert.async();
	let random = dataent.utils.get_random(10);
	dataent.run_serially([
		() => dataent.set_route('List', 'ToDo'),
		() => dataent.new_doc('ToDo'),
		() => dataent.quick_entry.dialog.set_value('description', random),
		() => dataent.quick_entry.insert(),
		() => {
			return dataent.tests.make('Report', [
				{report_name: 'ToDo List Report'},
				{report_type: 'Query Report'},
				{ref_doctype: 'ToDo'}
			]);
		},
		() => dataent.set_route('Form','Report', 'ToDo List Report'),

		//Query
		() => cur_frm.set_value('query','select description,owner,status from `tabToDo`'),
		() => cur_frm.save(),
		() => dataent.set_route('query-report','ToDo List Report'),	
		() => dataent.timeout(5),
		() => { 
			assert.ok($('div.slick-header-column').length == 4,'Correct numbers of columns visible');
			//To check if the result is present
			assert.ok($('div.r1:contains('+random+')').is(':visible'),'Result is visible in report');
			dataent.timeout(3);
		},
		() => done()
	]);
});
