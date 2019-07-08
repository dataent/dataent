// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

import showdown from 'showdown';

dataent.provide("dataent.tools");

dataent.tools.downloadify = function(data, roles, title) {
	if(roles && roles.length && !has_common(roles, roles)) {
		dataent.msgprint(__("Export not allowed. You need {0} role to export.", [dataent.utils.comma_or(roles)]));
		return;
	}

	var filename = title + ".csv";
	var csv_data = dataent.tools.to_csv(data);
	var a = document.createElement('a');

	if ("download" in a) {
		// Used Blob object, because it can handle large files
		var blob_object = new Blob([csv_data], { type: 'text/csv;charset=UTF-8' });
		a.href = URL.createObjectURL(blob_object);
		a.download = filename;

	} else {
		// use old method
		a.href = 'data:attachment/csv,' + encodeURIComponent(csv_data);
		a.download = filename;
		a.target = "_blank";
	}

	document.body.appendChild(a);
	a.click();

	document.body.removeChild(a);
};

dataent.markdown = function(txt) {
	if(!dataent.md2html) {
		dataent.md2html = new showdown.Converter();
	}

	while(txt.substr(0,1)==="\n") {
		txt = txt.substr(1);
	}

	// remove leading tab (if they exist in the first line)
	var whitespace_len = 0,
		first_line = txt.split("\n")[0];

	while(["\n", "\t"].indexOf(first_line.substr(0,1))!== -1) {
		whitespace_len++;
		first_line = first_line.substr(1);
	}

	if(whitespace_len && whitespace_len != first_line.length) {
		var txt1 = [];
		$.each(txt.split("\n"), function(i, t) {
			txt1.push(t.substr(whitespace_len));
		})
		txt = txt1.join("\n");
	}

	return dataent.md2html.makeHtml(txt);
}


dataent.tools.to_csv = function(data) {
	var res = [];
	$.each(data, function(i, row) {
		row = $.map(row, function(col) {
			if (col === null || col === undefined) col = '';
			return typeof col === "string" ? ('"' + $('<i>').html(col.replace(/"/g, '""')).text() + '"') : col;
		});
		res.push(row.join(","));
	});
	return res.join("\n");
};

dataent.slickgrid_tools = {
	get_filtered_items: function(dataView) {
		var data = [];
		for (var i=0, len=dataView.getLength(); i<len; i++) {
			// remove single quotes at start and end of total labels when print/pdf
			var obj = dataView.getItem(i);
			for (var item in obj) {
				if(obj.hasOwnProperty(item) && typeof(obj[item]) == "string"
					&& obj[item].charAt(0) == "'" && obj[item].charAt(obj[item].length -1) == "'") {
					dataView.getItem(i)[item] = obj[item].substr(1, obj[item].length-2);
				}
			}
			data.push(dataView.getItem(i));
		}
		return data;
	},
	get_view_data: function(columns, dataView, filter) {
		var col_row = $.map(columns, function(v) { return v.name; });
		var res = [];
		var col_map = $.map(columns, function(v) { return v.field; });

		for (var i=0, len=dataView.length; i<len; i++) {
			var d = dataView[i];
			var row = [];
			$.each(col_map, function(i, col) {
				var val = d[col];
				if(val===null || val===undefined) {
					val = "";
				}
				if(typeof(val) == "string") {
					// export to csv and get first or second column of the grid indented if it is. e.g: account_name
					if((i<3) && d['indent'] > 0 && (isNaN((new Date(val)).valueOf()))) {
						val = " ".repeat(d['indent'] * 8) + val;
					}
					// remove single quotes at start and end of total labels when export to csv
					if(val.charAt(0) == "'" && val.charAt(val.length -1) == "'") {
						val = val.substr(1, val.length-2);
					}
				}
				row.push(val);
			});

			if(!filter || filter(row, d)) {
				res.push(row);
			}
		}
		return [col_row].concat(res);
	},
	add_property_setter_on_resize: function(grid) {
		grid.onColumnsResized.subscribe(function(e, args) {
			$.each(grid.getColumns(), function(i, col) {
				if(col.docfield && col.previousWidth != col.width &&
					!in_list(dataent.model.std_fields_list, col.docfield.fieldname) ) {
					dataent.call({
						method:"dataent.client.make_width_property_setter",
						args: {
							doc: {
								doctype:'Property Setter',
								doctype_or_field: 'DocField',
								doc_type: col.docfield.parent,
								field_name: col.docfield.fieldname,
								property: 'width',
								value: col.width,
								"__islocal": 1
							}
						}
					});
					col.previousWidth = col.width;
					col.docfield.width = col.width;
				}
			});
		});
	}
};
