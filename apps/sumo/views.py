import json
import logging
import os
import socket
import StringIO
from time import time

import django
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import (HttpResponsePermanentRedirect, HttpResponseRedirect,
                         HttpResponse, Http404)
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from celery.messaging import establish_connection
from commonware.decorators import xframe_allow
import django_qunit.views
import jingo
from jinja2 import Markup
from PIL import Image
from session_csrf import anonymous_csrf

from sumo.redis_utils import redis_client, RedisError
from sumo.urlresolvers import reverse
from sumo.utils import get_next_url
from users.forms import AuthenticationForm


log = logging.getLogger('k.services')


def locales(request):
    """The locale switcher page."""

    return jingo.render(request, 'sumo/locales.html', dict(
        next_url=get_next_url(request) or reverse('home')))


@anonymous_csrf
def handle403(request):
    """A 403 message that looks nicer than the normal Apache forbidden page"""
    no_cookies = False
    referer = request.META.get('HTTP_REFERER')
    if referer:
        no_cookies = (referer.endswith(reverse('users.login'))
                      or referer.endswith(reverse('users.register')))

    return jingo.render(request, 'handlers/403.html',
                        {'form': AuthenticationForm(),
                         'no_cookies': no_cookies},
                        status=403)


def handle404(request):
    """A handler for 404s"""
    return jingo.render(request, 'handlers/404.html', status=404)


def handle500(request):
    """A 500 message that looks nicer than the normal Apache error page"""
    return jingo.render(request, 'handlers/500.html', status=500)


def redirect_to(request, url, permanent=True, **kwargs):
    """Like Django's redirect_to except that 'url' is passed to reverse."""
    dest = reverse(url, kwargs=kwargs)
    if permanent:
        return HttpResponsePermanentRedirect(dest)

    return HttpResponseRedirect(dest)


def deprecated_redirect(request, url, **kwargs):
    """Redirect with an interstitial page telling folks to update their
    bookmarks.
    """
    dest = reverse(url, kwargs=kwargs)
    proto = 'https://' if request.is_secure() else 'http://'
    host = Site.objects.get_current().domain
    return jingo.render(request, 'sumo/deprecated.html',
                        {'dest': dest, 'proto': proto, 'host': host})


def robots(request):
    """Generate a robots.txt."""
    if not settings.ENGAGE_ROBOTS:
        template = 'User-Agent: *\nDisallow: /'
    else:
        template = jingo.render(request, 'sumo/robots.html')
    return HttpResponse(template, mimetype='text/plain')


@never_cache
def monitor(request):

    # For each check, a boolean pass/fail to show in the template.
    status_summary = {}
    status = 200

    # Check all memcached servers.
    memcache_results = []
    status_summary['memcache'] = True
    for cache_name, cache_props in settings.CACHES.items():
        result = True
        backend = cache_props['BACKEND']
        location = cache_props['LOCATION']

        # LOCATION can be a string or a list of strings
        if isinstance(location, basestring):
            location = location.split(';')

        if 'memcache' in backend:
            for loc in location:
                # TODO: this doesn't handle unix: variant
                ip, port = loc.split(':')
                try:
                    s = socket.socket()
                    s.connect((ip, int(port)))
                except Exception, e:
                    result = False
                    status_summary['memcache'] = False
                    log.critical('Failed to connect to memcached (%s): %s' %
                                 (location, e))
                finally:
                    s.close()

                memcache_results.append((ip, port, result))

        if len(memcache_results) < 2:
            status_summary['memcache'] = False
            log.warning('You should have 2+ memcache servers.  You have %s.' %
                        len(memcache_results))

    if not memcache_results:
        status_summary['memcache'] = False
        log.warning('Memcache is not configured.')

    # Check Libraries and versions
    libraries_results = []
    status_summary['libraries'] = True
    try:
        Image.new('RGB', (16, 16)).save(StringIO.StringIO(), 'JPEG')
        libraries_results.append(('PIL+JPEG', True, 'Got it!'))
    except Exception, e:
        status_summary['libraries'] = False
        msg = "Failed to create a jpeg image: %s" % e
        libraries_results.append(('PIL+JPEG', False, msg))

    msg = 'We want read + write.'
    filepaths = (
        (settings.USER_AVATAR_PATH, os.R_OK | os.W_OK, msg),
        (settings.IMAGE_UPLOAD_PATH, os.R_OK | os.W_OK, msg),
        (settings.THUMBNAIL_UPLOAD_PATH, os.R_OK | os.W_OK, msg),
        (settings.GALLERY_IMAGE_PATH, os.R_OK | os.W_OK, msg),
        (settings.GALLERY_IMAGE_THUMBNAIL_PATH, os.R_OK | os.W_OK, msg),
        (settings.GALLERY_VIDEO_PATH, os.R_OK | os.W_OK, msg),
        (settings.GALLERY_VIDEO_THUMBNAIL_PATH, os.R_OK | os.W_OK, msg),
        (settings.GROUP_AVATAR_PATH, os.R_OK | os.W_OK, msg),
    )

    filepath_results = []
    filepath_status = True
    for path, perms, notes in filepaths:
        path = os.path.join(settings.MEDIA_ROOT, path)
        path_exists = os.path.isdir(path)
        path_perms = os.access(path, perms)
        filepath_status = filepath_status and path_exists and path_perms
        filepath_results.append((path, path_exists, path_perms, notes))

    status_summary['filepaths'] = filepath_status

    # Check RabbitMQ.
    rabbitmq_status = True
    rabbitmq_results = ''
    rabbit_conn = establish_connection(connect_timeout=2)
    try:
        rabbit_conn.connect()
        rabbitmq_results = 'Successfully connected to RabbitMQ.'
    except (socket.error, IOError), e:
        rabbitmq_results = Markup('There was an error connecting to RabbitMQ!'
                                  '<br/>%s' % str(e))
        rabbitmq_status = False
    status_summary['rabbitmq'] = rabbitmq_status

    # Check Celery.
    # start = time.time()
    # pong = celery.task.ping()
    # rabbit_results = r = {'duration': time.time() - start}
    # status_summary['rabbit'] = pong == 'pong' and r['duration'] < 1

    # Check Redis.
    redis_results = {}
    if hasattr(settings, 'REDIS_BACKENDS'):
        for backend in settings.REDIS_BACKENDS:
            try:
                c = redis_client(backend)
                redis_results[backend] = c.info()
            except RedisError:
                redis_results[backend] = False
    status_summary['redis'] = all(redis_results.values())

    if not all(status_summary.values()):
        status = 500

    return jingo.render(request, 'services/monitor.html',
                        {'memcache_results': memcache_results,
                         'libraries_results': libraries_results,
                         'filepath_results': filepath_results,
                         'rabbitmq_results': rabbitmq_results,
                         'redis_results': redis_results,
                         'status_summary': status_summary},
                         status=status)


@never_cache
def error(request):
    if not getattr(settings, 'STAGE', False):
        raise Http404
    # Do something stupid.
    fu


@require_GET
@never_cache
def version_check(request):
    mime = 'application/x-json'
    token = settings.VERSION_CHECK_TOKEN
    if (token is None or not 'token' in request.GET or
        token != request.GET['token']):
        return HttpResponse(status=403, mimetype=mime)

    versions = {
        'django': '.'.join(map(str, django.VERSION)),
    }
    return HttpResponse(json.dumps(versions), mimetype=mime)


# Allows another site to embed the QUnit suite
# in an iframe (for CI).
@xframe_allow
def kitsune_qunit(request, path):
    """View that hosts QUnit tests."""
    ctx = django_qunit.views.get_suite_context(request, path)
    ctx.update(timestamp=time())
    return jingo.render(request, 'tests/qunit.html', ctx)
