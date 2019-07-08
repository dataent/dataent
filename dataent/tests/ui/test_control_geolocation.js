QUnit.module('controls');

QUnit.test("Test ControlGeolocation", function(assert) {
	assert.expect(1);

	const random_name = dataent.utils.get_random(3).toLowerCase();

	let done = assert.async();

	// geolocation alert dialog suppressed (only secure origins or localhost allowed)
	window.alert = function() {
		console.log.apply(console, arguments); //eslint-disable-line
	};

	dataent.run_serially([
		() => {
			return dataent.tests.make('Custom Field', [
				{dt: 'ToDo'},
				{fieldtype: 'Geolocation'},
				{label: random_name},
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
			const control = $(`.dataent-control[data-fieldname="${random_name}"]`);

			return assert.ok(control.data('fieldtype') === 'Geolocation');
		},
		() => done()
	]);
});
