import json
import logging
import os
import socket
import StringIO

import django
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import (HttpResponsePermanentRedirect, HttpResponseRedirect,
                         HttpResponse, Http404)
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from celery.messaging import establish_connection
from mobility.decorators import mobile_template
from PIL import Image

from kitsune.lib.sumo_locales import LOCALES
from kitsune.search import es_utils
from kitsune.sumo.decorators import cors_enabled
from kitsune.sumo.redis_utils import redis_client, RedisError
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import get_next_url, uselocale
from kitsune.users.forms import AuthenticationForm


log = logging.getLogger('k.services')


@never_cache
@mobile_template('sumo/{mobile/}locales.html')
def locales(request, template):
    """The locale switcher page."""

    return render(request, template, dict(
        next_url=get_next_url(request) or reverse('home')))


def geoip_suggestion(request):
    """
    Ajax view to return the localized text for GeoIP locale change suggestion.

    Takes one parameter from the querystring:

        * locales - a form encoded list of locales to translate to.

    Example url: /localize?locales[]=es&locales[]=en-US
    """
    locales = request.GET.getlist('locales[]')

    response = {'locales': {}}
    for locale in locales:
        # English and native names for the language
        response['locales'][locale] = LOCALES.get(locale, '')
        with uselocale(locale):
            # This is using our JS-style string formatting.
            response[locale] = {
                'suggestion': _('Would you like to view this page in '
                                '%(language)s instead?'),
                'confirm': _('Yes'),
                'cancel': _('No'),
            }

    return HttpResponse(json.dumps(response), content_type='application/json')


def handle403(request):
    """A 403 message that looks nicer than the normal Apache forbidden page"""
    no_cookies = False
    referer = request.META.get('HTTP_REFERER')
    if referer:
        no_cookies = (referer.endswith(reverse('users.login')))

    return render(request, 'handlers/403.html', {
        'form': AuthenticationForm(),
        'no_cookies': no_cookies},
        status=403)


def handle404(request, *args, **kwargs):
    """A handler for 404s"""
    return render(request, 'handlers/404.html', status=404)


def handle500(request):
    """A 500 message that looks nicer than the normal Apache error page"""
    return render(request, 'handlers/500.html', status=500)


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
    return render(request, 'sumo/deprecated.html', {
        'dest': dest, 'proto': proto, 'host': host})


def robots(request):
    """Generate a robots.txt."""
    if not settings.ENGAGE_ROBOTS:
        template = 'User-Agent: *\nDisallow: /'
    else:
        template = render(request, 'sumo/robots.html')
    return HttpResponse(template, content_type='text/plain')


def test_memcached(host, port):
    """Connect to memcached.

    :returns: True if test passed, False if test failed.

    """
    try:
        s = socket.socket()
        s.connect((host, port))
        return True
    except Exception as exc:
        log.critical('Failed to connect to memcached (%r): %s' %
                     ((host, port), exc))
        return False
    finally:
        s.close()


ERROR = 'ERROR'
INFO = 'INFO'


@never_cache
def monitor(request):
    """View for services monitor."""
    status = {}

    # Note: To add a new component to the services monitor, do your
    # testing and then add a name -> list of output tuples map to
    # status.

    # Check memcached.
    memcache_results = []
    try:
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
                    result = test_memcached(ip, int(port))
                    memcache_results.append(
                        (INFO, '%s:%s %s' % (ip, port, result)))

        if not memcache_results:
            memcache_results.append((ERROR, 'memcache is not configured.'))

        elif len(memcache_results) < 2:
            memcache_results.append(
                (ERROR, ('You should have at least 2 memcache servers. '
                         'You have %s.' % len(memcache_results))))

        else:
            memcache_results.append((INFO, 'memcached servers look good.'))

    except Exception as exc:
        memcache_results.append(
            (ERROR, 'Exception while looking at memcached: %s' % str(exc)))

    status['memcached'] = memcache_results

    # Check Libraries and versions
    libraries_results = []
    try:
        Image.new('RGB', (16, 16)).save(StringIO.StringIO(), 'JPEG')
        libraries_results.append((INFO, 'PIL+JPEG: Got it!'))
    except Exception as exc:
        libraries_results.append(
            (ERROR,
             'PIL+JPEG: Probably missing: '
             'Failed to create a jpeg image: %s' % exc))

    status['libraries'] = libraries_results

    # Check file paths.
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
    for path, perms, notes in filepaths:
        path = os.path.join(settings.MEDIA_ROOT, path)
        path_exists = os.path.isdir(path)
        path_perms = os.access(path, perms)

        if path_exists and path_perms:
            filepath_results.append(
                (INFO, '%s: %s %s %s' % (path, path_exists, path_perms,
                                         notes)))

    status['filepaths'] = filepath_results

    # Check RabbitMQ.
    rabbitmq_results = []
    try:
        rabbit_conn = establish_connection(connect_timeout=5)
        rabbit_conn.connect()
        rabbitmq_results.append(
            (INFO, 'Successfully connected to RabbitMQ.'))
    except (socket.error, IOError) as exc:
        rabbitmq_results.append(
            (ERROR, 'Error connecting to RabbitMQ: %s' % str(exc)))

    except Exception as exc:
        rabbitmq_results.append(
            (ERROR, 'Exception while looking at RabbitMQ: %s' % str(exc)))

    status['RabbitMQ'] = rabbitmq_results

    # Check ES.
    es_results = []
    try:
        es_utils.get_doctype_stats(es_utils.all_read_indexes()[0])
        es_results.append(
            (INFO, ('Successfully connected to ElasticSearch and index '
                    'exists.')))

    except es_utils.ES_EXCEPTIONS as exc:
        es_results.append(
            (ERROR, 'ElasticSearch problem: %s' % str(exc)))

    except Exception as exc:
        es_results.append(
            (ERROR, 'Exception while looking at ElasticSearch: %s' % str(exc)))

    status['ElasticSearch'] = es_results

    # Check Celery.
    # start = time.time()
    # pong = celery.task.ping()
    # rabbit_results = r = {'duration': time.time() - start}
    # status_summary['rabbit'] = pong == 'pong' and r['duration'] < 1

    # Check Redis.
    redis_results = []
    if hasattr(settings, 'REDIS_BACKENDS'):
        for backend in settings.REDIS_BACKENDS:
            try:
                redis_client(backend)
                redis_results.append((INFO, '%s: Pass!' % backend))
            except RedisError:
                redis_results.append((ERROR, '%s: Fail!' % backend))
    status['Redis'] = redis_results

    status_code = 200

    status_summary = {}
    for component, output in status.items():
        if ERROR in [item[0] for item in output]:
            status_code = 500
            status_summary[component] = False
        else:
            status_summary[component] = True

    return render(request, 'services/monitor.html', {
        'component_status': status,
        'status_summary': status_summary},
        status=status_code)


@never_cache
def error(request):
    if not getattr(settings, 'STAGE', False):
        raise Http404
    # Do something stupid.
    fu  # noqa


@require_GET
@never_cache
def version_check(request):
    content_type = 'application/x-json'
    token = settings.VERSION_CHECK_TOKEN
    if (token is None or 'token' not in request.GET or
            token != request.GET['token']):
        return HttpResponse(status=403, content_type=content_type)

    versions = {
        'django': '.'.join(map(str, django.VERSION)),
    }
    return HttpResponse(json.dumps(versions), content_type=content_type)


@cors_enabled('*')
def serve_cors(*args, **kwargs):
    """A wrapper around django.views.static.serve that adds CORS headers."""
    if not settings.DEBUG:
        raise RuntimeError("Don't use kitsune.sumo.views.serve_cors "
                           "in production.")
    from django.views.static import serve
    return serve(*args, **kwargs)
