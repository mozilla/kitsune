"""
WSGI config for kitsune project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""
# newrelic import & initialization must come first
# https://docs.newrelic.com/docs/agents/python-agent/installation/python-agent-advanced-integration#manual-integration
try:
    import newrelic.agent
except ImportError:
    newrelic = False
else:
    newrelic.agent.initialize('newrelic.ini')

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitsune.settings')  # NOQA

from django.core.wsgi import get_wsgi_application

from decouple import config


application = get_wsgi_application()

if config('ENABLE_WHITENOISE', default=False, cast=bool):
    from whitenoise.django import DjangoWhiteNoise
    application = DjangoWhiteNoise(application)

# Add NewRelic
if newrelic:
    newrelic_license_key = config('NEW_RELIC_LICENSE_KEY', default=None)
    if newrelic_license_key:
        application = newrelic.agent.wsgi_application()(application)
