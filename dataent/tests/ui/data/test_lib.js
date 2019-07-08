dataent.tests = {
	data: {},
	make: function(doctype, data) {
		let dialog_is_active = () => {
			return (
				cur_dialog && (!cur_frm || cur_frm.doc.doctype != doctype)
			);
		};
		return dataent.run_serially([
			() => dataent.set_route('List', doctype),
			() => dataent.new_doc(doctype),
			() => {
				if (dataent.quick_entry) {
					dataent.quick_entry.dialog.$wrapper.find('.edit-full').click();
					return dataent.timeout(1);
				} else {
					let root_node;
					if (cur_tree) {
						for (const key in cur_tree.nodes) {
							if (cur_tree.nodes[key].parent_label && cur_tree.nodes[key].expandable) {
								root_node = cur_tree.nodes[key].label;
								break;
							}
						}
					}
					if (root_node){
						dataent.tests.open_add_child_dialog(root_node);
						return dataent.timeout(1);
					}
				}
			},
			() => {
				if(dialog_is_active()) {
					return dataent.tests.set_dialog_values(cur_dialog, data);
				} else {
					return dataent.tests.set_form_values(cur_frm, data);
				}
			},

			() => {
				if(dialog_is_active()) {
					return cur_dialog.get_primary_btn().click();
				} else {
					return dataent.quick_entry ? dataent.quick_entry.insert() : cur_frm.save();
				}
			}
		]);
	},
	open_add_child_dialog: (root_node) => {
		dataent.tests.click_link(root_node);
		dataent.timeout(1);
		dataent.tests.click_button('Add Child');
	},
	set_form_values: (frm, data) => {
		let tasks = [];

		data.forEach(item => {
			for (let key in item) {
				let task = () => {
					let value = item[key];
					if ($.isArray(value)) {
						return dataent.tests.set_grid_values(frm, key, value);
					} else {
						// single value
						return frm.set_value(key, value);
					}
				};
				tasks.push(task);
				tasks.push(dataent.after_ajax);
				tasks.push(() => dataent.timeout(0.4));
			}
		});

		// set values
		return dataent.run_serially(tasks);

	},
	set_dialog_values: (dialog, data) => {
		let tasks = [];

		data.forEach(item => {
			for (let key in item) {
				let task = () => {
					let value = item[key];
					return dialog.set_value(key, value);
				};
				tasks.push(task);
				tasks.push(dataent.after_ajax);
				tasks.push(() => dataent.timeout(0.4));
			}
		});

		return dataent.run_serially(tasks);
	},
	set_grid_values: (frm, key, value) => {
		// set value in grid
		let grid = frm.get_field(key).grid;
		grid.remove_all();

		let grid_row_tasks = [];

		// build tasks for each row
		value.forEach(d => {
			grid_row_tasks.push(() => {

				let grid_value_tasks = [];
				grid_value_tasks.push(() => grid.add_new_row());
				grid_value_tasks.push(() => grid.get_row(-1).toggle_view(true));
				grid_value_tasks.push(() => dataent.timeout(0.5));

				// build tasks to set each row value
				d.forEach(child_value => {
					for (let child_key in child_value) {
						grid_value_tasks.push(() => {
							let grid_row = grid.get_row(-1);
							return dataent.model.set_value(grid_row.doc.doctype,
								grid_row.doc.name, child_key, child_value[child_key]);
						});
						grid_value_tasks.push(dataent.after_ajax);
						grid_value_tasks.push(() => dataent.timeout(0.4));
					}
				});

				return dataent.run_serially(grid_value_tasks);
			});
		});
		return dataent.run_serially(grid_row_tasks);
	},
	setup_doctype: (doctype, data) => {
		return dataent.run_serially([
			() => dataent.set_route('List', doctype),
			() => dataent.timeout(1),
			() => {
				dataent.tests.data[doctype] = [];
				let expected = Object.keys(data);
				cur_list.data.forEach((d) => {
					dataent.tests.data[doctype].push(d.name);
					if(expected.indexOf(d.name) !== -1) {
						expected[expected.indexOf(d.name)] = null;
					}
				});

				let tasks = [];

				expected.forEach(function(d) {
					if(d) {
						tasks.push(() => dataent.tests.make(doctype,
							data[d]));
					}
				});

				return dataent.run_serially(tasks);
			}]);
	},
	click_page_head_item: (text) => {
		// Method to items present on the page header like New, Save, Delete etc.
		let  possible_texts = ["New", "Delete", "Save", "Yes"];
		return dataent.run_serially([
			() => {
				if (text == "Menu"){
					$(`span.menu-btn-group-label:contains('Menu'):visible`).click();
				} else if (text == "Refresh") {
					$(`.btn-secondary:contains('Refresh'):visible`).click();
				} else if (possible_texts.includes(text)) {
					$(`.btn-primary:contains("${text}"):visible`).click();
				}
			},
			() => dataent.timeout(1)
		]);
	},
	click_dropdown_item: (text) => {
		// Method to click dropdown elements
		return dataent.run_serially([
			() => {
				let li = $(`.dropdown-menu li:contains("${text}"):visible`).get(0);
				$(li).find(`a`).click();
			},
			() => dataent.timeout(1)
		]);
	},
	click_desktop_icon: (text) => {
		// Method to click the desktop icons on the Desk, by their name
		return dataent.run_serially([
			() => $("#icon-grid > div > div.app-icon[title="+text+"]").click(),
			() => dataent.timeout(1)
		]);
	},
	is_visible: (text, tag='a') => {
		// Method to check the visibility of an element
		return $(`${tag}:contains("${text}")`).is(`:visible`);
	},
	/**
	 * Clicks a button on a form.
	 * @param {String} text - The button's text
	 * @return {dataent.timeout}
	 * @throws will throw an exception if a matching visible button is not found
	 */
	click_button: function(text) {
		let element = $(`.btn:contains("${text}"):visible`);
		if(!element.length) {
			throw `did not find any button containing ${text}`;
		}
		element.click();
		return dataent.timeout(0.5);
	},
	/**
	 * Clicks a link on a form.
	 * @param {String} text - The text of the link to be clicked
	 * @return {dataent.timeout}
	 * @throws will throw an exception if a link with the given text is not found
	 */
	click_link: function(text) {
		let element = $(`a:contains("${text}"):visible`);
		if(!element.length) {
			throw `did not find any link containing ${text}`;
		}
		element.get(0).click();
		return dataent.timeout(0.5);
	},
	/**
	 * Sets the given control to the value given.
	 * @param {String} fieldname - The Doctype's field name
	 * @param {String} value - The value the control should be changed to
	 * @return {dataent.timeout}
	 * @throws will throw an exception if the field is not found or is not visible
	 */
	set_control: function(fieldname, value) {
		let control = $(`.form-control[data-fieldname="${fieldname}"]:visible`);
		if(!control.length) {
			throw `did not find any control with fieldname ${fieldname}`;
		}
		control.val(value).trigger('change');
		return dataent.timeout(0.5);
	},
	/**
	 * Checks if given field is disabled.
	 * @param {String} fieldname - The Doctype field name
	 * @return {Boolean} true if condition is met
	 * @throws will throw an exception if the field is not found or is not a form control
	 */
	is_disabled_field: function(fieldname){
		let control = $(`.form-control[data-fieldname="${fieldname}"]:disabled`);
		if(!control.length) {
			throw `did not find any control with fieldname ${fieldname}`;
		} else {
			return true;
		}
	}
};