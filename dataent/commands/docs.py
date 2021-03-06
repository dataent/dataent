from __future__ import unicode_literals, absolute_import
import click
import os, shutil
import dataent
from dataent.commands import pass_context

@click.command('build-docs')
@pass_context
@click.argument('app')
@click.option('--docs-version', default='current')
@click.option('--target', default=None)
@click.option('--local', default=False, is_flag=True, help='Run app locally')
@click.option('--watch', default=False, is_flag=True, help='Watch for changes and rewrite')
def build_docs(context, app, docs_version="current", target=None, local=False, watch=False):
	"Setup docs in target folder of target app"
	from dataent.utils import watch as start_watch
	from dataent.utils.setup_docs import add_breadcrumbs_tag

	for site in context.sites:
		_build_docs_once(site, app, docs_version, target, local)

		if watch:
			def trigger_make(source_path, event_type):
				if "/docs/user/" in source_path:
					# user file
					target_path = dataent.get_app_path(target, 'www', 'docs', 'user',
						os.path.relpath(source_path, start=dataent.get_app_path(app, 'docs', 'user')))
					shutil.copy(source_path, target_path)
					add_breadcrumbs_tag(target_path)

				if source_path.endswith('/docs/index.md'):
					target_path = dataent.get_app_path(target, 'www', 'docs', 'index.md')
					shutil.copy(source_path, target_path)

			apps_path = dataent.get_app_path(app)
			start_watch(apps_path, handler=trigger_make)

def _build_docs_once(site, app, docs_version, target, local, only_content_updated=False):
	from dataent.utils.setup_docs import setup_docs

	try:

		dataent.init(site=site)
		dataent.connect()
		make = setup_docs(app, target)

		if not only_content_updated:
			make.build(docs_version)

		#make.make_docs(target, local)

	finally:
		dataent.destroy()

commands = [
	build_docs,
]
