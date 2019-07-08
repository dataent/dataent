// try and delete a standard row, it should fail

QUnit.module('Customize Form');

QUnit.test("test customize form", function(assert) {
	assert.expect(2);
	let done = assert.async();
	dataent.run_serially([
		() => dataent.set_route('Form', 'Customize Form'),
		() => dataent.timeout(1),
		() => cur_frm.set_value('doc_type', 'ToDo'),
		() => dataent.timeout(2),
		() => {
			// find the status column as there may be other custom fields like
			// kanban etc.
			dataent.row_idx = 0;
			cur_frm.doc.fields.every((d, i) => {
				if(d.fieldname==='status') {
					dataent.row_idx = i;
					return false;
				} else {
					return true;
				}
			});
			assert.equal(cur_frm.doc.fields[dataent.row_idx].fieldname, 'status',
				'check if selected field is "status"');
		},
		// open "status" row
		() => cur_frm.fields_dict.fields.grid.grid_rows[dataent.row_idx].toggle_view(),
		() => dataent.timeout(0.5),

		// try deleting it
		() => $('.grid-delete-row:visible').click(),

		() => dataent.timeout(0.5),
		() => dataent.hide_msgprint(),
		() => dataent.timeout(0.5),

		// status still exists
		() => assert.equal(cur_frm.doc.fields[dataent.row_idx].fieldname, 'status',
			'check if selected field is still "status"'),
		() => done()
	]);
});
