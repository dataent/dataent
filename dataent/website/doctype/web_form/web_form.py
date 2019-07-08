# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent, json, os
from dataent.website.website_generator import WebsiteGenerator
from dataent import _, scrub
from dataent.utils import cstr
from dataent.utils.file_manager import save_file, remove_file_by_url
from dataent.website.utils import get_comment_list
from dataent.custom.doctype.customize_form.customize_form import docfield_properties
from dataent.utils.file_manager import get_max_file_size
from dataent.modules.utils import export_module_json, get_doc_module
from six.moves.urllib.parse import urlencode
from dataent.integrations.utils import get_payment_gateway_controller
from six import iteritems


class WebForm(WebsiteGenerator):
	website = dataent._dict(
		no_cache = 1
	)

	def onload(self):
		super(WebForm, self).onload()
		if self.is_standard and not dataent.conf.developer_mode:
			self.use_meta_fields()

	def validate(self):
		super(WebForm, self).validate()

		if not self.module:
			self.module = dataent.db.get_value('DocType', self.doc_type, 'module')

		if (not (dataent.flags.in_install or dataent.flags.in_patch or dataent.flags.in_test or dataent.flags.in_fixtures)
			and self.is_standard and not dataent.conf.developer_mode):
			dataent.throw(_("You need to be in developer mode to edit a Standard Web Form"))

		if not dataent.flags.in_import:
			self.validate_fields()

		if self.accept_payment:
			self.validate_payment_amount()

	def validate_fields(self):
		'''Validate all fields are present'''
		from dataent.model import no_value_fields
		missing = []
		meta = dataent.get_meta(self.doc_type)
		for df in self.web_form_fields:
			if df.fieldname and (df.fieldtype not in no_value_fields and not meta.has_field(df.fieldname)):
				missing.append(df.fieldname)

		if missing:
			dataent.throw(_('Following fields are missing:') + '<br>' + '<br>'.join(missing))

	def validate_payment_amount(self):
		if self.amount_based_on_field and not self.amount_field:
			dataent.throw(_("Please select a Amount Field."))
		elif not self.amount_based_on_field and not self.amount > 0:
			dataent.throw(_("Amount must be greater than 0."))


	def reset_field_parent(self):
		'''Convert link fields to select with names as options'''
		for df in self.web_form_fields:
			df.parent = self.doc_type

	def use_meta_fields(self):
		'''Override default properties for standard web forms'''
		meta = dataent.get_meta(self.doc_type)

		for df in self.web_form_fields:
			meta_df = meta.get_field(df.fieldname)

			if not meta_df:
				continue

			for prop in docfield_properties:
				if df.fieldtype==meta_df.fieldtype and prop not in ("idx",
					"reqd", "default", "description", "default", "options",
					"hidden", "read_only", "label"):
					df.set(prop, meta_df.get(prop))


			# TODO translate options of Select fields like Country

	# export
	def on_update(self):
		"""
			Writes the .txt for this page and if write_content is checked,
			it will write out a .html file
		"""
		path = export_module_json(self, self.is_standard, self.module)

		if path:
			# js
			if not os.path.exists(path + '.js'):
				with open(path + '.js', 'w') as f:
					f.write("""dataent.ready(function() {
	// bind events here
})""")

			# py
			if not os.path.exists(path + '.py'):
				with open(path + '.py', 'w') as f:
					f.write("""from __future__ import unicode_literals

import dataent

def get_context(context):
	# do your magic here
	pass
""")

	def get_context(self, context):
		'''Build context to render the `web_form.html` template'''
		self.set_web_form_module()

		context._login_required = False
		if self.login_required and dataent.session.user == "Guest":
			context._login_required = True

		doc, delimeter = make_route_string(dataent.form_dict)
		context.doc = doc
		context.delimeter = delimeter

		# check permissions
		if dataent.session.user == "Guest" and dataent.form_dict.name:
			dataent.throw(_("You need to be logged in to access this {0}.").format(self.doc_type), dataent.PermissionError)

		if dataent.form_dict.name and not has_web_form_permission(self.doc_type, dataent.form_dict.name):
			dataent.throw(_("You don't have the permissions to access this document"), dataent.PermissionError)

		self.reset_field_parent()

		if self.is_standard:
			self.use_meta_fields()

		if not context._login_required:
			if self.allow_edit:
				if self.allow_multiple:
					if not dataent.form_dict.name and not dataent.form_dict.new:
						self.build_as_list(context)
				else:
					if dataent.session.user != 'Guest' and not dataent.form_dict.name:
						dataent.form_dict.name = dataent.db.get_value(self.doc_type, {"owner": dataent.session.user}, "name")

					if not dataent.form_dict.name:
						# only a single doc allowed and no existing doc, hence new
						dataent.form_dict.new = 1

		# always render new form if login is not required or doesn't allow editing existing ones
		if not self.login_required or not self.allow_edit:
			dataent.form_dict.new = 1

		self.load_document(context)
		context.parents = self.get_parents(context)

		if self.breadcrumbs:
			context.parents = dataent.safe_eval(self.breadcrumbs, { "_": _ })

		context.has_header = ((dataent.form_dict.name or dataent.form_dict.new)
			and (dataent.session.user!="Guest" or not self.login_required))

		if context.success_message:
			context.success_message = dataent.db.escape(context.success_message.replace("\n",
				"<br>"))

		self.add_custom_context_and_script(context)
		if not context.max_attachment_size:
			context.max_attachment_size = get_max_file_size() / 1024 / 1024

		context.show_in_grid = self.show_in_grid

	def load_document(self, context):
		'''Load document `doc` and `layout` properties for template'''
		if dataent.form_dict.name or dataent.form_dict.new:
			context.layout = self.get_layout()
			context.parents = [{"route": self.route, "label": _(self.title) }]

		if dataent.form_dict.name:
			context.doc = dataent.get_doc(self.doc_type, dataent.form_dict.name)
			context.title = context.doc.get(context.doc.meta.get_title_field())
			context.doc.add_seen()

			context.reference_doctype = context.doc.doctype
			context.reference_name = context.doc.name

			if self.allow_comments:
				context.comment_list = get_comment_list(context.doc.doctype,
					context.doc.name)

	def build_as_list(self, context):
		'''Web form is a list, show render as list.html'''
		from dataent.www.list import get_context as get_list_context

		# set some flags to make list.py/list.html happy
		dataent.form_dict.web_form_name = self.name
		dataent.form_dict.doctype = self.doc_type
		dataent.flags.web_form = self

		self.update_params_from_form_dict(context)
		self.update_list_context(context)
		get_list_context(context)
		context.is_list = True

	def update_params_from_form_dict(self, context):
		'''Copy params from list view to new view'''
		context.params_from_form_dict = ''

		params = {}
		for key, value in iteritems(dataent.form_dict):
			if dataent.get_meta(self.doc_type).get_field(key):
				params[key] = value

		if params:
			context.params_from_form_dict = '&' + urlencode(params)


	def update_list_context(self, context):
		'''update list context for stanard modules'''
		if hasattr(self, 'web_form_module') and hasattr(self.web_form_module, 'get_list_context'):
			self.web_form_module.get_list_context(context)

	def get_payment_gateway_url(self, doc):
		if self.accept_payment:
			controller = get_payment_gateway_controller(self.payment_gateway)

			title = "Payment for {0} {1}".format(doc.doctype, doc.name)
			amount = self.amount
			if self.amount_based_on_field:
				amount = doc.get(self.amount_field)
			payment_details = {
				"amount": amount,
				"title": title,
				"description": title,
				"reference_doctype": doc.doctype,
				"reference_docname": doc.name,
				"payer_email": dataent.session.user,
				"payer_name": dataent.utils.get_fullname(dataent.session.user),
				"order_id": doc.name,
				"currency": self.currency,
				"redirect_to": dataent.utils.get_url(self.route)
			}

			# Redirect the user to this url
			return controller.get_payment_url(**payment_details)

	def add_custom_context_and_script(self, context):
		'''Update context from module if standard and append script'''
		if self.web_form_module:
			new_context = self.web_form_module.get_context(context)

			if new_context:
				context.update(new_context)

			js_path = os.path.join(os.path.dirname(self.web_form_module.__file__), scrub(self.name) + '.js')
			if os.path.exists(js_path):
				context.script = dataent.render_template(open(js_path, 'r').read(), context)

			css_path = os.path.join(os.path.dirname(self.web_form_module.__file__), scrub(self.name) + '.css')
			if os.path.exists(css_path):
				context.style = open(css_path, 'r').read()

	def get_layout(self):
		layout = []
		def add_page(df=None):
			new_page = {'sections': []}
			layout.append(new_page)
			if df and df.fieldtype=='Page Break':
				new_page.update(df.as_dict())

			return new_page

		def add_section(df=None):
			new_section = {'columns': []}
			if layout:
				layout[-1]['sections'].append(new_section)
			if df and df.fieldtype=='Section Break':
				new_section.update(df.as_dict())

			return new_section

		def add_column(df=None):
			new_col = []
			if layout:
				layout[-1]['sections'][-1]['columns'].append(new_col)

			return new_col

		page, section, column = None, None, None
		for df in self.web_form_fields:

			# breaks
			if df.fieldtype=='Page Break':
				page = add_page(df)
				section, column = None, None

			if df.fieldtype=='Section Break':
				section = add_section(df)
				column = None

			if df.fieldtype=='Column Break':
				column = add_column(df)

			# input
			if df.fieldtype not in ('Section Break', 'Column Break', 'Page Break'):
				if not page:
					page = add_page()
					section, column = None, None
				if not section:
					section = add_section()
					column = None
				if column==None:
					column = add_column()
				column.append(df)

		return layout

	def get_parents(self, context):
		parents = None

		if context.is_list and not context.parents:
			parents = [{"title": _("My Account"), "name": "me"}]
		elif context.parents:
			parents = context.parents

		return parents

	def set_web_form_module(self):
		'''Get custom web form module if exists'''
		if self.is_standard:
			self.web_form_module = get_doc_module(self.module, self.doctype, self.name)
		else:
			self.web_form_module = None

	def validate_mandatory(self, doc):
		'''Validate mandatory web form fields'''
		missing = []
		for f in self.web_form_fields:
			if f.reqd and doc.get(f.fieldname) in (None, [], ''):
				missing.append(f)

		if missing:
			dataent.throw(_('Mandatory Information missing:') + '<br><br>'
				+ '<br>'.join(['{0} ({1})'.format(d.label, d.fieldtype) for d in missing]))


@dataent.whitelist(allow_guest=True)
def accept(web_form, data, for_payment=False):
	'''Save the web form'''
	data = dataent._dict(json.loads(data))
	files = []
	files_to_delete = []

	web_form = dataent.get_doc("Web Form", web_form)
	if data.doctype != web_form.doc_type:
		dataent.throw(_("Invalid Request"))

	elif data.name and not web_form.allow_edit:
		dataent.throw(_("You are not allowed to update this Web Form Document"))

	dataent.flags.in_web_form = True
	meta = dataent.get_meta(data.doctype)

	if data.name:
		# update
		doc = dataent.get_doc(data.doctype, data.name)
	else:
		# insert
		doc = dataent.new_doc(data.doctype)

	# set values
	for field in web_form.web_form_fields:
		fieldname = field.fieldname
		df = meta.get_field(fieldname)
		value = data.get(fieldname, None)

		if df and df.fieldtype in ('Attach', 'Attach Image'):
			if value and 'data:' and 'base64' in value:
				files.append((fieldname, value))
				if not doc.name:
					doc.set(fieldname, '')
				continue

			elif not value and doc.get(fieldname):
				files_to_delete.append(doc.get(fieldname))

		doc.set(fieldname, value)

	if for_payment:
		web_form.validate_mandatory(doc)
		doc.run_method('validate_payment')

	if doc.name:
		if has_web_form_permission(doc.doctype, doc.name, "write"):
			doc.save(ignore_permissions=True)
		else:
			# only if permissions are present
			doc.save()

	else:
		# insert
		if web_form.login_required and dataent.session.user=="Guest":
			dataent.throw(_("You must login to submit this form"))

		ignore_mandatory = True if files else False

		doc.insert(ignore_permissions = True, ignore_mandatory = ignore_mandatory)

	# add files
	if files:
		for f in files:
			fieldname, filedata = f

			# remove earlier attached file (if exists)
			if doc.get(fieldname):
				remove_file_by_url(doc.get(fieldname), doc.doctype, doc.name)

			# save new file
			filename, dataurl = filedata.split(',', 1)
			filedoc = save_file(filename, dataurl,
				doc.doctype, doc.name, decode=True)

			# update values
			doc.set(fieldname, filedoc.file_url)

		doc.save(ignore_permissions = True)

	if files_to_delete:
		for f in files_to_delete:
			if f:
				remove_file_by_url(f, doc.doctype, doc.name)

	dataent.flags.web_form_doc = doc

	if for_payment:
		return web_form.get_payment_gateway_url(doc)
	else:
		return doc.as_dict()

@dataent.whitelist()
def delete(web_form_name, docname):
	web_form = dataent.get_doc("Web Form", web_form_name)

	owner = dataent.db.get_value(web_form.doc_type, docname, "owner")
	if dataent.session.user == owner and web_form.allow_delete:
		dataent.delete_doc(web_form.doc_type, docname, ignore_permissions=True)
	else:
		raise dataent.PermissionError("Not Allowed")


@dataent.whitelist()
def delete_multiple(web_form_name, docnames):
	web_form = dataent.get_doc("Web Form", web_form_name)

	docnames = json.loads(docnames)

	allowed_docnames = []
	restricted_docnames = []

	for docname in docnames:
		owner = dataent.db.get_value(web_form.doc_type, docname, "owner")
		if dataent.session.user == owner and web_form.allow_delete:
			allowed_docnames.append(docname)
		else:
			restricted_docnames.append(docname)

	for docname in allowed_docnames:
		dataent.delete_doc(web_form.doc_type, docname, ignore_permissions=True)

	if restricted_docnames:
		raise dataent.PermissionError("You do not have permisssion to delete " + ", ".join(restricted_docnames))


def has_web_form_permission(doctype, name, ptype='read'):
	if dataent.session.user=="Guest":
		return False

	# owner matches
	elif dataent.db.get_value(doctype, name, "owner")==dataent.session.user:
		return True

	elif dataent.has_website_permission(name, ptype=ptype, doctype=doctype):
		return True

	elif check_webform_perm(doctype, name):
		return True

	else:
		return False


def check_webform_perm(doctype, name):
	doc = dataent.get_doc(doctype, name)
	if hasattr(doc, "has_webform_permission"):
		if doc.has_webform_permission():
			return True

def get_web_form_list(doctype, txt, filters, limit_start, limit_page_length=20, order_by=None):
	from dataent.www.list import get_list
	if not filters:
		filters = {}

	filters["owner"] = dataent.session.user

	return get_list(doctype, txt, filters, limit_start, limit_page_length, order_by=order_by,
		ignore_permissions=True)

def make_route_string(parameters):
	route_string = ""
	delimeter = '?'
	if isinstance(parameters, dict):
		for key in parameters:
			if key != "web_form_name":
				route_string += route_string + delimeter + key + "=" + cstr(parameters[key])
				delimeter = '&'
	return (route_string, delimeter)

@dataent.whitelist(allow_guest=True)
def get_form_data(doctype, docname=None, web_form_name=None):
	out = dataent._dict()

	if docname:
		doc = dataent.get_doc(doctype, docname)
		if has_web_form_permission(doctype, docname, ptype='read'):
			out.doc = doc
		else:
			dataent.throw(_("Not permitted"), dataent.PermissionError)

	out.web_form = dataent.get_doc('Web Form', web_form_name)

	# For Table fields, server-side processing for meta
	for field in out.web_form.web_form_fields:
		if field.fieldtype == "Table":
			field.fields = get_in_list_view_fields(field.options)
			out.update({field.fieldname: field.fields})

		if field.fieldtype == "Link":
			field.fieldtype = "Autocomplete"
			field.options = get_link_options(
				web_form_name,
				field.options,
				field.allow_read_on_all_link_options
			)

	return out

@dataent.whitelist()
def get_in_list_view_fields(doctype):
	return [df.as_dict() for df in dataent.get_meta(doctype).fields if df.in_list_view]

@dataent.whitelist(allow_guest=True)
def get_link_options(web_form_name, doctype, allow_read_on_all_link_options=False):
	web_form_doc = dataent.get_doc("Web Form", web_form_name)
	doctype_validated = False
	limited_to_user   = False
	if web_form_doc.login_required:
		# check if dataent session user is not guest or admin
		if dataent.session.user != 'Guest':
			doctype_validated = True

			if not allow_read_on_all_link_options:
				limited_to_user   = True

	else:
		for field in web_form_doc.web_form_fields:
			if field.options == doctype:
				doctype_validated = True
				break

	if doctype_validated:
		link_options = []
		if limited_to_user:
			link_options = "\n".join([doc.name for doc in dataent.get_all(doctype, filters = {"owner":dataent.session.user})])
		else:
			link_options = "\n".join([doc.name for doc in dataent.get_all(doctype)])

		return link_options

	else:
		raise dataent.PermissionError('Not Allowed, {0}'.format(doctype))

