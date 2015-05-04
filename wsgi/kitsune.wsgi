import os
import site
from datetime import datetime

try:
    import newrelic.agent
except ImportError:
    newrelic = False


if newrelic:
    newrelic_ini = os.getenv('NEWRELIC_PYTHON_INI_FILE', False)
    if newrelic_ini:
        newrelic.agent.initialize(newrelic_ini)
    else:
        newrelic = False


# Remember when mod_wsgi loaded this file so we can track it in nagios.
wsgi_loaded = datetime.now()

# Add kitsune to the python path
wsgidir = os.path.dirname(__file__)
site.addsitedir(os.path.abspath(os.path.join(wsgidir, '../')))

# For django-celery
os.environ['CELERY_LOADER'] = 'django'

# Activate virtualenv
activate_env = os.path.abspath(os.path.join(wsgidir, "../virtualenv/bin/activate_this.py"))
execfile(activate_env, dict(__file__=activate_env))

# Import for side-effects: set-up
import manage

import django.conf
# import django.core.management
# import django.utils

# Do validate and activate translations like using `./manage.py runserver`.
# http://blog.dscpl.com.au/2010/03/improved-wsgi-script-for-use-with.html
# django.utils.translation.activate(django.conf.settings.LANGUAGE_CODE)
# utility = django.core.management.ManagementUtility()
# command = utility.fetch_command('runserver')
# command.validate()

# This is what mod_wsgi runs.
from django.core.wsgi import get_wsgi_application
django_app = get_wsgi_application()

# Normally we could let WSGIHandler run directly, but while we're dark
# launching, we want to force the script name to be empty so we don't create
# any /z links through reverse.  This fixes bug 554576.
def application(env, start_response):
    if 'HTTP_X_ZEUS_DL_PT' in env:
        env['SCRIPT_URL'] = env['SCRIPT_NAME'] = ''
    env['wsgi.loaded'] = wsgi_loaded
    env['platform.name'] = django.conf.settings.PLATFORM_NAME

    if newrelic:
        return newrelic.agent.wsgi_application()(
            django_app)(env, start_response)

    return django_app(env, start_response)


# Uncomment this to figure out what's going on with the mod_wsgi environment.
# def application(env, start_response):
#     start_response('200 OK', [('Content-Type', 'text/plain')])
#     return '\n'.join('%r: %r' % item for item in sorted(env.items()))

# vim: ft=python
