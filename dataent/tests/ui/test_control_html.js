QUnit.module('controls');

QUnit.test("Test ControlHTML", function(assert) {
	assert.expect(3);
	const random_name = dataent.utils.get_random(3).toLowerCase();

	let done = assert.async();

	dataent.run_serially([
		() => {
			return dataent.tests.make('Custom Field', [
				{dt: 'ToDo'},
				{fieldtype: 'HTML'},
				{label: random_name},
				{options: '<h3> Test </h3>'}
			]);
		},
		() => {
			return dataent.tests.make('Custom Field', [
				{dt: 'ToDo'},
				{fieldtype: 'HTML'},
				{label: random_name + "_template"},
				{options: '<h3> Test {{ doc.status }} </h3>'}
			]);
		},
		() => dataent.set_route('List', 'ToDo'),
		() => dataent.new_doc('ToDo'),
		() => {
			if (dataent.quick_entry)
			{
				dataent.quick_entry.dialog.$wrapper.find('.edit-full').click();
				return dataent.timeout(1);
			}
		},
		() => {
			const control = $(`.dataent-control[data-fieldname="${random_name}"]`)[0];

			return assert.ok(control.innerHTML === '<h3> Test </h3>');
		},
		() => {
			const control = $(`.dataent-control[data-fieldname="${random_name}_template"]`)[0];
			// refresh input must be called independently
			cur_frm.get_field(`${random_name}_template`).refresh_input();

			return assert.ok(control.innerHTML === '<h3> Test Open </h3>');
		},
		() => dataent.tests.set_control("status", "Closed"),
		() => dataent.timeout(1),
		() => {
			const control = $(`.dataent-control[data-fieldname="${random_name}_template"]`)[0];
			// refresh input must be called independently
			cur_frm.get_field(`${random_name}_template`).refresh_input();
			return assert.ok(control.innerHTML === '<h3> Test Closed </h3>');
		},
		() => done()
	]);
});
