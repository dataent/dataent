/* eslint-disable */
// rename this file from _test_[name] to test_[name] to activate
// and remove above this line

QUnit.test("test: Print Style", function (assert) {
	let done = assert.async();

	// number of asserts
	assert.expect(1);

	dataent.run_serially([
		// insert a new Print Style
		() => dataent.tests.make('Print Style', [
			// values to be set
			{print_style_name: 'Test Print Style'},
			{css: '/* some css value */'}
		]),
	]);

});
