QUnit.module('Core');

QUnit.test("test: Role Profile", function (assert) {
	let done = assert.async();

	assert.expect(3);

	dataent.run_serially([
		// insert a new user
		() => dataent.tests.make('Role Profile', [
			{role_profile: 'Test 2'}
		]),

		() => {
			$('input.box')[0].checked = true;
			$('input.box')[2].checked = true;
			$('input.box')[4].checked = true;
			cur_frm.save();
		},

		() => dataent.timeout(1),
		() => cur_frm.refresh(),
		() => dataent.timeout(2),
		() => {
			assert.equal($('input.box')[0].checked, true);
			assert.equal($('input.box')[2].checked, true);
			assert.equal($('input.box')[4].checked, true);
		},

		() => done()
	]);

});