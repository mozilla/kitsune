import json
import re
import sys
from contextlib import contextmanager
from datetime import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import pre_delete
from django.utils import translation
from django.utils.http import urlencode, is_safe_url

from ratelimit.utils import is_ratelimited as rl_is_ratelimited

from kitsune.sumo import paginator
from kitsune.journal.models import Record


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
def chunked(seq, n, length=None):
    """
    Yield successive n-sized chunks from seq.

    If length isn't specifed, it is calculated from len(seq).

    >>> for group in chunked(range(8), 3):
    ...     print group
    [0, 1, 2]
    [3, 4, 5]
    [6, 7]
    """
    if not length:
        length = len(seq)
    for i in xrange(0, length, n):
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
        try:
            field_class = sender._meta.get_field(field_name)
        except models.FieldDoesNotExist:
            # This works around a weird issue in Django 1.7.
            continue
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

    if not settings.DEBUG and not is_safe_url(url, Site.objects.get_current().domain):
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


@contextmanager
def uselocale(locale):
    """
    Context manager for setting locale and returning to previous locale.

    This is useful for when doing translations for things run by
    celery workers or out of the HTTP request handling path. Example:

        with uselocale('xx'):
            subj = _('Subject of my email')
            msg = render_email(email_template, email_kwargs)
            mail.send_mail(subj, msg, ...)

    In Kitsune, you can get the right locale from Profile.locale and
    also request.LANGUAGE_CODE.

    If Kitsune is handling an HTTP request already, you don't have to
    run uselocale---the locale will already be set correctly.

    """
    currlocale = translation.get_language()
    translation.activate(locale)
    yield
    translation.activate(currlocale)


def rabbitmq_queue_size():
    """Returns the rabbitmq queue size.

    Two things to know about the queue size:

    1. It's not 100% accurate, but the size is generally near that
       number

    2. I can't think of a second thing, but that first thing is
       pretty important.

    """
    # FIXME: 2015-04-23: This is busted.

    from celery import current_app

    # FIXME: This uses a private method, but I'm not sure how else to
    # figure this out, either.
    app = current_app._get_current_object()
    conn = app.connection()
    chan = conn.default_channel

    # FIXME: This hard-codes the exchange, but I'm not sure how else
    # to figure it out.
    queue = chan.queue_declare('celery', passive=True)
    return queue.message_count


class Progress(object):
    """A widget to show progress during interactive CLI scripts.

    Example:

        prog = Progress(100)
        prog.draw()
        for i in range(100):
            time.sleep(0.1)
            prog.tick()

    This will draw a progress indicator that looks like

        55/100 (Est 0 min. remaining)

    TODO
    * Improve the time estimation, it's quite bad.
    * Display a progress bar.
    * Use Blessings instead of manually moving the cursor around.
    * Dynamically pick time units.
    * Pick an approriate stride instead of a hard coded one.
        * Or pick a better stats method that doesn't use a stride.
    """

    def __init__(self, total, milestone_stride=10):
        """
        :param total: The number of items the progress bar will expect.
        :param milestone_stide: Number of items between stats calculations.
            Default: 10
        """
        self.current = 0
        self.total = total
        self.milestone_stride = milestone_stride
        self.milestone_time = datetime.now()
        self.estimated = '?'

    def tick(self, incr=1):
        """Advance the current progress, and redraw the screen.

        :param incr: Raise the current progress by this amount. Default: 1
        """
        self.current += incr

        if self.current and self.current % self.milestone_stride == 0:
            now = datetime.now()
            duration = now - self.milestone_time
            duration = duration.seconds + duration.microseconds / 1e6
            rate = self.milestone_stride / duration
            remaining = self.total - self.current
            self.estimated = int(remaining / rate / 60)
            self.milestone_time = now

        self.draw()

    def draw(self):
        """Just redraw the screen."""
        self._wr('{0.current}/{0.total} (Est. {0.estimated} min. remaining)\r'
                 .format(self))

    def _wr(self, s):
        sys.stdout.write(s)
        sys.stdout.flush()


def is_ratelimited(request, name, rate, method=['POST'], skip_if=lambda r: False):
    """
    Reimplement ``ratelimit.helpers.is_ratelimited``, with sumo-specific details:

    * Always check for the bypass rate limit permission.
    * Log times when users are rate limited.
    * Always uses ``user_or_ip`` for the rate limit key.
    """
    if skip_if(request) or request.user.has_perm('sumo.bypass_ratelimit'):
        request.limited = False
    else:
        # TODO: make sure 'group' value below is sufficient
        # TODO: make sure 'user_or_ip' is a valid replacement for
        # old/deleted custom user_or_ip method
        rl_is_ratelimited(request, increment=True, group='sumo.utils.is_ratelimited',
                          rate=rate, key='user_or_ip')
        if request.limited:
            if hasattr(request, 'user') and request.user.is_authenticated():
                key = 'user "{}"'.format(request.user.username)
            else:
                ip = request.META.get('HTTP_X_CLUSTER_CLIENT_IP', request.META['REMOTE_ADDR'])
                key = 'anonymous user ({})'.format(ip)
            Record.objects.info('sumo.ratelimit', '{key} hit the rate limit for {name}',
                                key=key, name=name)
    return request.limited


def get_browser(user_agent):
    """Get Browser Name from User Agent"""

    match = re.search(r'(?i)(firefox|msie|chrome|safari|trident)', user_agent, re.IGNORECASE)
    if match:
        browser = match.group(1)
    else:
        browser = None
    return browser
