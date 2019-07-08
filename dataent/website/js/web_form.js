import WebForm from './web_form_class';
import make_datatable from './grid_list';

dataent.ready(function() {
	if(web_form_settings.is_list) {
		$('body').show();
		if($('.web-form-list').length) {
			make_datatable('.web-form-list', web_form_settings.web_form_doctype);
		}
		return;
	}

	dataent.form_dirty = false;
	$.extend(dataent, web_form_settings);
	moment.defaultFormat = dataent.moment_date_format;
	$('[data-toggle="tooltip"]').tooltip();

	const { web_form_doctype: doctype, doc_name: docname, web_form_name } = web_form_settings;
	const wrapper = $(`.webform-wrapper`);
	var $form = $("div[data-web-form='"+dataent.web_form_name+"']");

	// :( Needed by core model, meta and perm, all now included in th website js
	// One of the few non-touchy options
	dataent.boot.user = {
		can_read: '', can_write: '', can_create: ''
	};

	dataent.web_form = new WebForm({
		wrapper: wrapper,
		doctype: doctype,
		docname: docname,
		web_form_name: web_form_name,
		allow_incomplete: dataent.allow_incomplete
	});

	setTimeout(() => {
		$('body').css('display', 'block');

		// remove footer save button if form height is less than window height
		if($('.webform-wrapper').height() < window.innerHeight) {
			$(".footer-button").addClass("hide");
		}

		if (dataent.init_client_script) {
			dataent.init_client_script();

			if (dataent.web_form.after_load) {
				dataent.web_form.after_load();
			}
		}
	}, 500);

	// allow payment only if
	$('.btn-payment').on('click', function() {
		save(true);
		return false;
	});

	// submit
	$(".btn-form-submit").on("click", function() {
		save();
		return false;
	});

	// change section
	$('.btn-change-section, .slide-progress .fa-fw').on('click', function() {
		var idx = $(this).attr('data-idx');
		if(!dataent.form_dirty || dataent.is_read_only) {
			show_slide(idx);
		} else {
			if(save() !== false) {
				show_slide(idx);
			}
		}
		return false;
	});

	var show_slide = function(idx) {
		// hide all sections
		$('.web-form-page').addClass('hidden');

		// slide-progress
		$('.slide-progress .fa-circle')
			.removeClass('fa-circle').addClass('fa-circle-o');
		$('.slide-progress .fa-fw[data-idx="'+idx+'"]')
			.removeClass('fa-circle-o').addClass('fa-circle');

		// un hide target section
		$('.web-form-page[data-idx="'+idx+'"]')
			.removeClass('hidden')
			.find(':input:first').focus();

	};

	function save(for_payment) {
		if (dataent.web_form.validate()===false) {
			return false;
		}

		let data = dataent.web_form.get_values();
		if (!data) {
			return false;
		}

		if (window.saving) {
			return false;
		}

		window.saving = true;
		dataent.form_dirty = false;

		dataent.call({
			type: "POST",
			method: "dataent.website.doctype.web_form.web_form.accept",
			args: {
				data: data,
				web_form: dataent.web_form_name,
				for_payment: for_payment
			},
			freeze: true,
			btn: $form.find("[type='submit']"),
			callback: function(data) {
				if(!data.exc) {
					dataent.doc_name = data.message.name;
					if(!dataent.login_required) {
						show_success_message();
					}

					if(dataent.is_new && dataent.login_required) {
						// reload page (with ID)
						window.location.href = window.location.pathname + "?name=" + dataent.doc_name;
					}

					if(for_payment && data.message) {
						// redirect to payment
						window.location.href = data.message;
					}

					// refresh values
					if (dataent.web_form) {
						dataent.web_form.field_group.set_values(data.message);
					}

				} else {
					dataent.msgprint(__('There were errors. Please report this.'));
				}
			},
			always: function() {
				window.saving = false;
			}
		});
		return true;
	}

	function show_success_message() {
		$form.addClass("hide");
		$(".comments, .introduction, .page-head").addClass("hide");
		scroll(0, 0);
		set_message(dataent.success_link, true);
	}

	function set_message(msg, permanent) {
		$(".form-message")
			.html(msg)
			.removeClass("hide");

		if(!permanent) {
			setTimeout(function() {
				$(".form-message").addClass('hide');
			}, 5000);
		}
	}

	// close button
	$(".close").on("click", function() {
		var name = $(this).attr("data-name");
		if(name) {
			dataent.call({
				type:"POST",
				method: "dataent.website.doctype.web_form.web_form.delete",
				args: {
					"web_form": dataent.web_form_name,
					"name": name
				},
				callback: function(r) {
					if(!r.exc) {
						location.reload();
					}
				}
			});
		}
	});
});
