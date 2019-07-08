dataent.provide("dataent.integration_service")

dataent.integration_service.razorpay = {
	load: function(frm) {
		new dataent.integration_service.Razorpay(frm)
	},
	scheduler_job_helper: function(){
		return  {
			"Every few minutes": "Check and capture new payments"
		}
	}
}

dataent.integration_service.Razorpay =  Class.extend({
	init:function(frm){
		this.frm = frm;
		this.frm.toggle_display("use_test_account", false);
		this.show_logs();
	},
	show_logs: function(){
		this.frm.add_custom_button(__("Show Log"), function(frm){
			dataent.route_options = {"integration_request_service": "Razorpay"};
			dataent.set_route("List", "Integration Request");
		});
	}
})
