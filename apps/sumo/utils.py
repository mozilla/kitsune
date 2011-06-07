import urlparse

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import parse_backend_uri
from django.db import models
from django.db.models.signals import pre_delete
from django.utils.http import urlencode

from redis import Redis

from sumo import paginator


def paginate(request, queryset, per_page=20, count=None):
    """Get a Paginator, abstracting some common paging actions."""
    p = paginator.Paginator(queryset, per_page, count=count)

    # Get the page from the request, make sure it's an int.
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    # Get a page of results, or the first page if there's a problem.
    try:
        paginated = p.page(page)
    except (paginator.EmptyPage, paginator.InvalidPage):
        paginated = p.page(1)

    base = request.build_absolute_uri(request.path)

    items = [(k, v) for k in request.GET if k != 'page'
             for v in request.GET.getlist(k) if v]

    qsa = urlencode(items)

    paginated.url = u'%s?%s' % (base, qsa)
    return paginated


# By Ned Batchelder.
def chunked(seq, n):
    """
    Yield successive n-sized chunks from seq.

    >>> for group in chunked(range(8), 3):
    ...     print group
    [0, 1, 2]
    [3, 4, 5]
    [6, 7]
    """
    for i in xrange(0, len(seq), n):
        yield seq[i:i + n]


def smart_int(string, fallback=0):
    """Convert a string to int, with fallback for invalid strings or types."""
    try:
        return int(float(string))
    except (ValueError, TypeError, OverflowError):
        return fallback


def delete_files_for_obj(sender, **kwargs):
    """Signal receiver of a model class and instance. Deletes its files."""
    obj = kwargs.pop('instance')
    for field_name in sender._meta.get_all_field_names():
        # Skip related models' attrs.
        if not hasattr(obj, field_name):
            continue
        # Get the class and value of the field.
        field_class = sender._meta.get_field(field_name)
        field_value = getattr(obj, field_name)
        # Check if it's a FileField instance and the field is set.
        if isinstance(field_class, models.FileField) and field_value:
            field_value.delete()


def auto_delete_files(cls):
    """Deletes all FileFields when model instances are deleted.

    Meant to be used on model classes.
    Django disabled auto-deletion of files when deleting a model in
    ticket #6456, to prevent dataloss.

    """
    pre_delete.connect(delete_files_for_obj, sender=cls)
    return cls


def get_next_url(request):
    """Given a request object, looks for the best possible next URL.

    Useful for e.g. redirects back to original page after a POST request.

    """
    if 'next' in request.POST:
        url = request.POST.get('next')
    elif 'next' in request.GET:
        url = request.GET.get('next')
    else:
        url = request.META.get('HTTP_REFERER')

    if url:
        parsed_url = urlparse.urlparse(url)
        # Don't redirect outside of SUMO.
        # Don't include protocol+domain, so if we are https we stay that way.
        if parsed_url.scheme:
            site_domain = Site.objects.get_current().domain
            url_domain = parsed_url.netloc
            if site_domain != url_domain:
                url = None
            else:
                url = u'?'.join([getattr(parsed_url, x) for x in
                                ('path', 'query') if getattr(parsed_url, x)])

        # Don't redirect right back to login or logout page
        if parsed_url.path in [settings.LOGIN_URL, settings.LOGOUT_URL]:
            url = None

    return url


def redis_client(name):
    """Get a Redis client.

    Uses the name argument to lookup the connection string in the
    settings.REDIS_BACKEND dict.
    """
    uri = settings.REDIS_BACKENDS[name]
    _, server, params = parse_backend_uri(uri)
    db = params.pop('db', 1)
    try:
        db = int(db)
    except (ValueError, TypeError):
        db = 1
    try:
        socket_timeout = float(params.pop('socket_timeout'))
    except (KeyError, ValueError):
        socket_timeout = None
    password = params.pop('password', None)
    if ':' in server:
        host, port = server.split(':')
        try:
            port = int(port)
        except (ValueError, TypeError):
            port = 6379
    else:
        host = server
        port = 6379
    return Redis(host=host, port=port, db=db, password=password,
                 socket_timeout=socket_timeout)
