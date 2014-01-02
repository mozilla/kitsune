from contextlib import contextmanager
import json

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import pre_delete
from django.utils import translation
from django.utils.http import urlencode, is_safe_url

import tower

from mozillapulse.publishers import SUMOPublisher

from kitsune.sumo import paginator


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

    paginated.url = build_paged_url(request)

    return paginated


def simple_paginate(request, queryset, per_page=20):
    """Get a SimplePaginator page."""
    p = paginator.SimplePaginator(queryset, per_page)

    # Let the view the handle exceptions.
    page = p.page(request.GET.get('page', 1))
    page.url = build_paged_url(request)

    return page


def build_paged_url(request):
    """Build the url for the paginator."""
    base = request.build_absolute_uri(request.path)

    items = [(k, v) for k in request.GET if k != 'page'
             for v in request.GET.getlist(k) if v]

    qsa = urlencode(items)

    return u'%s?%s' % (base, qsa)


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

    if not is_safe_url(url, Site.objects.get_current().domain):
        return None

    return url


class TruncationException(Exception):
    pass


def truncated_json_dumps(obj, max_length, key, ensure_ascii=False):
    """Dump an object to JSON, and ensure the dump is less than ``max_length``.

    The truncation will happen by truncating ``obj[key]``. If ``key`` is not
    long enough to achieve the goal, an exception will be thrown.

    If ``ensure_ascii`` is ``True``, the value returned will be only ASCII,
    even if that means representing Unicode characters as escape sequences. If
    ``False``, a Unicode string will be returned without escape sequences. The
    default is ``False``. This is the same as the ``ensure_ascii`` paramater on
    ``json.dumps``.
    """
    orig = json.dumps(obj, ensure_ascii=ensure_ascii)
    diff = len(orig) - max_length
    if diff < 0:
        # No need to truncate
        return orig
    # Make a copy, so that we don't modify the original
    dupe = json.loads(orig)
    if len(dupe[key]) < diff:
        raise TruncationException("Can't truncate enough to satisfy "
                                  "`max_length`.")
    dupe[key] = dupe[key][:-diff]
    return json.dumps(dupe, ensure_ascii=ensure_ascii)


def user_or_ip(key_prefix):
    """Used for generating rate limiting keys. Returns a function to pass on
    to rate limit. The function return returns a key with IP address for
    anonymous users, and pks for authenticated users.

    Examples
        Anonymous: 'uip:<key_prefix>:127.0.0.1'
        Authenticated: 'uip:<key_prefix>:17859'
    """

    def _user_or_ip(request):
        if hasattr(request, 'user') and request.user.is_authenticated():
            key = str(request.user.pk)
        else:
            key = request.META.get('HTTP_X_CLUSTER_CLIENT_IP',
                                   request.META['REMOTE_ADDR'])
        return 'uip:%s:%s' % (key_prefix, key)

    return _user_or_ip


@contextmanager
def uselocale(locale):
    """Context manager for setting locale and returning
    to previous locale.

    This is useful for when doing translations for things run by
    celery workers or out of the HTTP request handling path.

    >>> with uselocale('xx'):
    ...     subj = _('Subject of my email')
    ...     msg = render_email(email_template, email_kwargs)
    ...     mail.send_mail(subj, msg, ...)
    ...

    In Kitsune, you can get the right locale from Profile.locale and
    also request.LANGUAGE_CODE.

    If Kitsune is handling an HTTP request already, you don't have to
    run uselocale---the locale will already be set correctly.

    """
    currlocale = translation.get_language()
    tower.activate(locale)
    yield
    tower.activate(currlocale)


def publish_message(message):
    publisher = SUMOPublisher(host=settings.RABBIT_HOST,
                              port=settings.RABBIT_PORT,
                              vhost=settings.RABBIT_VHOST,
                              user=settings.RABBIT_USER,
                              password=settings.RABBIT_PASSWORD)
    try:
        publisher.publish(message)
    except Exception as e:
        import sys
        print >>sys.stderr, 'error: ' + str(e)
        #XXX handle stuff
        pass
