import re
import sys

from django import http
from django.conf import settings as django_settings
from django.contrib import admin
from django.db import connection
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views import debug

import celery.conf
import jinja2
from redis import ConnectionError

from kitsune.sumo.redis_utils import redis_client


def settings(request):
    """Admin view that displays the django settings."""
    settings = debug.get_safe_settings()
    sorted_settings = [{'key': key, 'value': settings[key]} for
                       key in sorted(settings.keys())]

    return render_to_response('kadmin/settings.html',
                              {'pythonpath': sys.path,
                               'settings': sorted_settings,
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


def redis_info(request):
    """Admin view that displays redis INFO+CONFIG output for all backends."""
    redis_info = {}
    for key in django_settings.REDIS_BACKENDS.keys():
        redis_info[key] = {}
        client = redis_client(key)
        redis_info[key]['connection'] = django_settings.REDIS_BACKENDS[key]
        try:
            cfg = client.config_get()
            redis_info[key]['config'] = [{'key': k, 'value': cfg[k]} for k in
                                         sorted(cfg)]
            info = client.info()
            redis_info[key]['info'] = [{'key': k, 'value': info[k]} for k in
                                       sorted(info)]
        except ConnectionError:
            redis_info[key]['down'] = True

    return render_to_response('kadmin/redis.html',
                              {'redis_info': redis_info,
                               'title': 'Redis Information'},
                              RequestContext(request, {}))

admin.site.register_view('redis', redis_info,
                         'Redis Information')
