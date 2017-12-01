"""
WSGI config for kitsune project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitsune.settings')  # NOQA

from django.core.handlers.wsgi import WSGIRequest
from django.core.wsgi import get_wsgi_application

from decouple import config


IS_HTTPS = config('HTTPS', default='off', cast=bool)
# For django-celery
os.environ['CELERY_LOADER'] = 'django'


class WSGIHTTPSRequest(WSGIRequest):
    def _get_scheme(self):
        if IS_HTTPS:
            return 'https'

        return super(WSGIHTTPSRequest, self)._get_scheme()


application = get_wsgi_application()
application.request_class = WSGIHTTPSRequest

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
