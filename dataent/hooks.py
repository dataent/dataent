from __future__ import unicode_literals
from . import __version__ as app_version


app_name = "dataent"
app_title = "Dataent Framework"
app_publisher = "Dataent Technologies"
app_description = "Full stack web framework with Python, Javascript, MariaDB, Redis, Node"
app_icon = "octicon octicon-circuit-board"
app_color = "orange"
source_link = "https://github.com/dataent/dataent"
app_license = "MIT"

develop_version = '12.x.x-develop'

app_email = "info@epaas.xyz"

docs_app = "dataent_io"

before_install = "dataent.utils.install.before_install"
after_install = "dataent.utils.install.after_install"

page_js = {
	"setup-wizard": "public/js/dataent/setup_wizard.js"
}

# website
app_include_js = [
	"assets/js/libs.min.js",
	"assets/js/desk.min.js",
	"assets/js/list.min.js",
	"assets/js/form.min.js",
	"assets/js/control.min.js",
	"assets/js/report.min.js",
	"assets/dataent/js/dataent/toolbar.js"
]
app_include_css = [
	"assets/css/desk.min.css",
	"assets/css/list.min.css",
	"assets/css/form.min.css",
	"assets/css/report.min.css",
	"assets/css/module.min.css"
]

web_include_js = [
	"website_script.js"
]

bootstrap = "assets/dataent/css/bootstrap.css"
web_include_css = [
	"assets/css/dataent-web.css"
]

website_route_rules = [
	{"from_route": "/blog/<category>", "to_route": "Blog Post"},
	{"from_route": "/kb/<category>", "to_route": "Help Article"},
	{"from_route": "/newsletters", "to_route": "Newsletter"}
]

write_file_keys = ["file_url", "file_name"]

notification_config = "dataent.core.notifications.get_notification_config"

before_tests = "dataent.utils.install.before_tests"

email_append_to = ["Event", "ToDo", "Communication"]

get_rooms = 'dataent.chat.doctype.chat_room.chat_room.get_rooms'

calendars = ["Event"]

# login

on_session_creation = [
	"dataent.core.doctype.activity_log.feed.login_feed",
	"dataent.core.doctype.user.user.notify_admin_access_to_system_manager",
	"dataent.limits.check_if_expired",
	"dataent.utils.scheduler.reset_enabled_scheduler_events",
]

# permissions

permission_query_conditions = {
	"Event": "dataent.desk.doctype.event.event.get_permission_query_conditions",
	"ToDo": "dataent.desk.doctype.todo.todo.get_permission_query_conditions",
	"User": "dataent.core.doctype.user.user.get_permission_query_conditions",
	"Note": "dataent.desk.doctype.note.note.get_permission_query_conditions",
	"Kanban Board": "dataent.desk.doctype.kanban_board.kanban_board.get_permission_query_conditions",
	"Contact": "dataent.contacts.address_and_contact.get_permission_query_conditions_for_contact",
	"Address": "dataent.contacts.address_and_contact.get_permission_query_conditions_for_address",
	"Communication": "dataent.core.doctype.communication.communication.get_permission_query_conditions_for_communication",
	"Workflow Action": "dataent.workflow.doctype.workflow_action.workflow_action.get_permission_query_conditions"
}

has_permission = {
	"Event": "dataent.desk.doctype.event.event.has_permission",
	"ToDo": "dataent.desk.doctype.todo.todo.has_permission",
	"User": "dataent.core.doctype.user.user.has_permission",
	"Note": "dataent.desk.doctype.note.note.has_permission",
	"Kanban Board": "dataent.desk.doctype.kanban_board.kanban_board.has_permission",
	"Contact": "dataent.contacts.address_and_contact.has_permission",
	"Address": "dataent.contacts.address_and_contact.has_permission",
	"Communication": "dataent.core.doctype.communication.communication.has_permission",
	"Workflow Action": "dataent.workflow.doctype.workflow_action.workflow_action.has_permission"
}

has_website_permission = {
	"Address": "dataent.contacts.doctype.address.address.has_website_permission"
}

standard_queries = {
	"User": "dataent.core.doctype.user.user.user_query"
}

doc_events = {
	"*": {
		"on_update": [
			"dataent.desk.notifications.clear_doctype_notifications",
			"dataent.core.doctype.activity_log.feed.update_feed",
			"dataent.workflow.doctype.workflow_action.workflow_action.process_workflow_actions"
		],
		"after_rename": "dataent.desk.notifications.clear_doctype_notifications",
		"on_cancel": [
			"dataent.desk.notifications.clear_doctype_notifications",
			"dataent.workflow.doctype.workflow_action.workflow_action.process_workflow_actions"
		],
		"on_trash": [
			"dataent.desk.notifications.clear_doctype_notifications",
			"dataent.workflow.doctype.workflow_action.workflow_action.process_workflow_actions"
		],
		"on_change": [
			"dataent.core.doctype.feedback_trigger.feedback_trigger.trigger_feedback_request",
		]
	},
	"Email Group Member": {
		"validate": "dataent.email.doctype.email_group.email_group.restrict_email_group"
	},

}

scheduler_events = {
	"all": [
		"dataent.email.queue.flush",
		"dataent.email.doctype.email_account.email_account.pull",
		"dataent.email.doctype.email_account.email_account.notify_unreplied",
		"dataent.oauth.delete_oauth2_data",
		"dataent.integrations.doctype.razorpay_settings.razorpay_settings.capture_payment",
		"dataent.twofactor.delete_all_barcodes_for_users",
		"dataent.integrations.doctype.gcalendar_settings.gcalendar_settings.sync",
		"dataent.website.doctype.web_page.web_page.check_publish_status",
		'dataent.utils.global_search.sync_global_search'
	],
	"hourly": [
		"dataent.model.utils.link_count.update_link_count",
		'dataent.model.utils.user_settings.sync_user_settings',
		"dataent.utils.error.collect_error_snapshots",
		"dataent.desk.page.backups.backups.delete_downloadable_backups",
		"dataent.limits.update_space_usage",
		"dataent.limits.update_site_usage",
		"dataent.desk.doctype.auto_repeat.auto_repeat.make_auto_repeat_entry",
	],
	"daily": [
		"dataent.email.queue.clear_outbox",
		"dataent.desk.notifications.clear_notifications",
		"dataent.core.doctype.error_log.error_log.set_old_logs_as_seen",
		"dataent.desk.doctype.event.event.send_event_digest",
		"dataent.sessions.clear_expired_sessions",
		"dataent.email.doctype.notification.notification.trigger_daily_alerts",
		"dataent.realtime.remove_old_task_logs",
		"dataent.utils.scheduler.disable_scheduler_on_expiry",
		"dataent.utils.scheduler.restrict_scheduler_events_if_dormant",
		"dataent.email.doctype.auto_email_report.auto_email_report.send_daily",
		"dataent.core.doctype.feedback_request.feedback_request.delete_feedback_request",
		"dataent.core.doctype.activity_log.activity_log.clear_authentication_logs",
	],
	"daily_long": [
		"dataent.integrations.doctype.dropbox_settings.dropbox_settings.take_backups_daily",
		"dataent.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_daily"
	],
	"weekly_long": [
		"dataent.integrations.doctype.dropbox_settings.dropbox_settings.take_backups_weekly",
		"dataent.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_weekly",
		"dataent.utils.change_log.check_for_update"
	],
	"monthly": [
		"dataent.email.doctype.auto_email_report.auto_email_report.send_monthly"
	],
	"monthly_long": [
		"dataent.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_monthly"
	]
}

get_translated_dict = {
	("doctype", "System Settings"): "dataent.geo.country_info.get_translated_dict",
	("page", "setup-wizard"): "dataent.geo.country_info.get_translated_dict"
}

sounds = [
	{"name": "email", "src": "/assets/dataent/sounds/email.mp3", "volume": 0.1},
	{"name": "submit", "src": "/assets/dataent/sounds/submit.mp3", "volume": 0.1},
	{"name": "cancel", "src": "/assets/dataent/sounds/cancel.mp3", "volume": 0.1},
	{"name": "delete", "src": "/assets/dataent/sounds/delete.mp3", "volume": 0.05},
	{"name": "click", "src": "/assets/dataent/sounds/click.mp3", "volume": 0.05},
	{"name": "error", "src": "/assets/dataent/sounds/error.mp3", "volume": 0.1},
	{"name": "alert", "src": "/assets/dataent/sounds/alert.mp3", "volume": 0.2},
	# {"name": "chime", "src": "/assets/dataent/sounds/chime.mp3"},

	# dataent.chat sounds
	{ "name": "chat-message", 	   "src": "/assets/dataent/sounds/chat-message.mp3",      "volume": 0.1 },
	{ "name": "chat-notification", "src": "/assets/dataent/sounds/chat-notification.mp3", "volume": 0.1 }
	# dataent.chat sounds
]

bot_parsers = [
	'dataent.utils.bot.ShowNotificationBot',
	'dataent.utils.bot.GetOpenListBot',
	'dataent.utils.bot.ListBot',
	'dataent.utils.bot.FindBot',
	'dataent.utils.bot.CountBot'
]

setup_wizard_exception = "dataent.desk.page.setup_wizard.setup_wizard.email_setup_wizard_exception"
before_write_file = "dataent.limits.validate_space_limit"

before_migrate = ['dataent.patches.v11_0.sync_user_permission_doctype_before_migrate.execute']

otp_methods = ['OTP App','Email','SMS']
