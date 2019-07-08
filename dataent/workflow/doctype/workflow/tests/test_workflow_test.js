QUnit.module('setup');

QUnit.test("Test Workflow", function(assert) {
	assert.expect(5);
	let done = assert.async();

	dataent.run_serially([
		() => dataent.set_route('Form', 'User', 'New User 1'),
		() => dataent.timeout(1),
		() => {
			cur_frm.set_value('email', 'test1@testmail.com');
			cur_frm.set_value('first_name', 'Test Name');
			cur_frm.set_value('send_welcome_email', 0);
			return cur_frm.save();
		},
		() => dataent.tests.click_button('Actions'),
		() => dataent.timeout(0.5),
		() => {
			let review = $(`.dropdown-menu li:contains("Review"):visible`).size();
			let approve = $(`.dropdown-menu li:contains("Approve"):visible`).size();
			assert.equal(review, 1, "Review Action exists");
			assert.equal(approve, 1, "Approve Action exists");
		},
		() => dataent.tests.click_dropdown_item('Approve'),
		() => dataent.timeout(1),
		() => dataent.tests.click_button('Yes'),
		() => dataent.timeout(1),
		() => {
			assert.equal($('.msgprint').text(), "Did not saveInsufficient Permission for User", "Approve action working");
			dataent.tests.click_button('Close');
		},
		() => dataent.timeout(1),
		() => {
			cur_frm.set_value('role_profile_name', 'Test 2');
			return cur_frm.save();
		},
		() => dataent.tests.click_button('Actions'),
		() => dataent.timeout(1),
		() => {
			let reject = $(`.dropdown-menu li:contains("Reject"):visible`).size();
			assert.equal(reject, 1, "Reject Action exists");
		},
		() => dataent.tests.click_dropdown_item('Reject'),
		() => dataent.timeout(1),
		() =>	{
			if(dataent.tests.click_button('Close'))
				assert.equal(1, 1, "Reject action works");
		},
		() => done()
	]);
});