// Copyright (c) 2017, Dataent Technologies and contributors
// For license information, please see license.txt

dataent.ui.form.on('Test Runner', {
	refresh: (frm) => {
		frm.disable_save();
		frm.page.set_primary_action(__("Run Tests"), () => {
			return new Promise(resolve => {
				let wrapper = $(frm.fields_dict.output.wrapper).empty();
				$("<p>Loading...</p>").appendTo(wrapper);

				// all tests
				dataent.call({
					method: 'dataent.core.doctype.test_runner.test_runner.get_test_js',
					args: { test_path: frm.doc.module_path }
				}).always((data) => {
					$("<div id='qunit'></div>").appendTo(wrapper.empty());
					frm.events.run_tests(frm, data.message);
					resolve();
				});
			});
		});

	},
	run_tests: function(frm, files) {
		dataent.flags.in_test = true;
		let require_list = [
			"assets/dataent/js/lib/jquery/qunit.js",
			"assets/dataent/js/lib/jquery/qunit.css"
		].concat();

		dataent.require(require_list, () => {
			files.forEach((f) => {
				dataent.dom.eval(f.script);
			});

			QUnit.config.notrycatch = true;

			window.onerror = function(msg, url, lineNo, columnNo, error) {
				console.log(error.stack); // eslint-disable-line
				$('<div id="dataent-qunit-done"></div>').appendTo($('body'));
			};

			QUnit.testDone(function(details) {
				// var result = {
				// 	"Module name": details.module,
				// 	"Test name": details.name,
				// 	"Assertions": {
				// 		"Total": details.total,
				// 		"Passed": details.passed,
				// 		"Failed": details.failed
				// 	},
				// 	"Skipped": details.skipped,
				// 	"Todo": details.todo,
				// 	"Runtime": details.runtime
				// };

				// eslint-disable-next-line
				// console.log(JSON.stringify(result, null, 2));

				details.assertions.map(a => {
					// eslint-disable-next-line
					console.log(`${a.result ? '✔' : '✗'}  ${a.message}`);
				});

			});
			QUnit.load();

			QUnit.done(({ total, failed, passed, runtime }) => {
				// flag for selenium that test is done

				console.log( `Total: ${total}, Failed: ${failed}, Passed: ${passed}, Runtime: ${runtime}` );  // eslint-disable-line

				if(failed) {
					console.log('Tests Failed'); // eslint-disable-line
				} else {
					console.log('Tests Passed'); // eslint-disable-line
				}
				dataent.set_route('Form', 'Test Runner', 'Test Runner');

				$('<div id="dataent-qunit-done"></div>').appendTo($('body'));

			});
		});

	}
});
