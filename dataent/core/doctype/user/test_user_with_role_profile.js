QUnit.module('Core');

QUnit.test("test: Set role profile in user", function (assert) {
	let done = assert.async();

	assert.expect(3);

	dataent.run_serially([

		// Insert a new user
		() => dataent.tests.make('User', [
			{email: 'test@test2.com'},
			{first_name: 'Test 2'},
			{send_welcome_email: 0}
		]),

		() => dataent.timeout(2),
		() => {
			return dataent.tests.set_form_values(cur_frm, [
				{role_profile_name:'Test 2'}
			]);
		},

		() => cur_frm.save(),
		() => dataent.timeout(2),

		() => {
			assert.equal($('input.box')[0].checked, true);
			assert.equal($('input.box')[2].checked, true);
			assert.equal($('input.box')[4].checked, true);
		},
		() => done()
	]);

});
