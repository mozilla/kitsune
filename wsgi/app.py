"""
WSGI config for kitsune project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitsune.settings')  # NOQA

from django.core.wsgi import get_wsgi_application

from decouple import config


# For django-celery
os.environ['CELERY_LOADER'] = 'django'

application = get_wsgi_application()

if config('SENTRY_DSN', None):
    from raven.contrib.django.raven_compat.middleware.wsgi import Sentry
    application = Sentry(application)

if config('ENABLE_WHITENOISE', default=False, cast=bool):
    from whitenoise.django import DjangoWhiteNoise
    application = DjangoWhiteNoise(application)

# Add NewRelic
newrelic_ini = config('NEW_RELIC_CONFIG_FILE', default='newrelic.ini')
newrelic_license_key = config('NEW_RELIC_LICENSE_KEY', default=None)
if newrelic_ini and newrelic_license_key:
    import newrelic.agent
    newrelic.agent.initialize(newrelic_ini)
    application = newrelic.agent.wsgi_application()(application)
