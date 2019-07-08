dataent.provide('dataent.ui.misc');
dataent.ui.misc.about = function() {
	if(!dataent.ui.misc.about_dialog) {
		var d = new dataent.ui.Dialog({title: __('Dataent Framework')});

		$(d.body).html(repl("<div>\
		<p>"+__("Open Source Applications for the Web")+"</p>  \
		<p><i class='fa fa-globe fa-fw'></i>\
			Website: <a href='https://epaas.xyz' target='_blank'>https://epaas.xyz</a></p>\
		<p><i class='fa fa-github fa-fw'></i>\
			Source: <a href='https://github.com/dataent' target='_blank'>https://github.com/dataent</a></p>\
		<hr>\
		<h4>Installed Apps</h4>\
		<div id='about-app-versions'>Loading versions...</div>\
		<hr>\
		<p class='text-muted'>&copy; Dataent Technologies Pvt. Ltd and contributors </p> \
		</div>", dataent.app));

		dataent.ui.misc.about_dialog = d;

		dataent.ui.misc.about_dialog.on_page_show = function() {
			if(!dataent.versions) {
				dataent.call({
					method: "dataent.utils.change_log.get_versions",
					callback: function(r) {
						show_versions(r.message);
					}
				})
			}
		};

		var show_versions = function(versions) {
			var $wrap = $("#about-app-versions").empty();
			$.each(Object.keys(versions).sort(), function(i, key) {
				var v = versions[key];
				if(v.branch) {
					var text = $.format('<p><b>{0}:</b> v{1} ({2})<br></p>',
						[v.title, v.branch_version || v.version, v.branch])
				} else {
					var text = $.format('<p><b>{0}:</b> v{1}<br></p>',
						[v.title, v.version])
				}
				$(text).appendTo($wrap);
			});

			dataent.versions = versions;
		}

	}

	dataent.ui.misc.about_dialog.show();

}
