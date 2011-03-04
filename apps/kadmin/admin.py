import re

from django import http
from django.contrib import admin
from django.db import connection
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views import debug

import celery.conf
import jinja2


def settings(request):
    """Admin view that displays the django settings."""
    settings = debug.get_safe_settings()
    sorted_settings = [{'key': key, 'value': settings[key]} for
                       key in sorted(settings.keys())]

    return render_to_response('kadmin/settings.html',
                              {'settings': sorted_settings,
                               'title': 'Settings'},
                              RequestContext(request, {}))

admin.site.register_view('settings', settings, 'Settings')


def celery_settings(request):
    """Admin view that displays the celery configuration."""
    capital = re.compile('^[A-Z]')
    settings = [key for key in dir(celery.conf) if capital.match(key)]
    sorted_settings = [{'key': key, 'value': '*****' if 'password' in
                        key.lower() else getattr(celery.conf, key)} for
                       key in sorted(settings)]

    return render_to_response('kadmin/settings.html',
                              {'settings': sorted_settings,
                               'title': 'Celery Settings'},
                              RequestContext(request, {}))

admin.site.register_view('celery', celery_settings, 'Celery Settings')


def env(request):
    """Admin view that displays the wsgi env."""
    return http.HttpResponse(u'<pre>%s</pre>' % (jinja2.escape(request)))

admin.site.register_view('env', env, 'WSGI Environment')


def schema_version(request):
    """Admin view that displays the current schema_version."""
    cursor = connection.cursor()
    cursor.execute('SELECT version FROM schema_version')
    version = [x for x in cursor][0][0]
    return render_to_response('kadmin/schema.html',
                              {'schema_version': version,
                               'title': 'Schema Version'},
                              RequestContext(request, {}))

admin.site.register_view('schema', schema_version,
                         'Database Schema Version')
