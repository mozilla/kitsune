import json
import re
import sys
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import pre_delete
from django.templatetags.static import static
from django.utils import translation
from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django_ratelimit.core import is_ratelimited as is_ratelimited_core
from timeout_decorator import timeout

from kitsune.journal.models import Record
from kitsune.lib.tlds import VALID_TLDS
from kitsune.sumo import paginator


POTENTIAL_LINK_REGEX = re.compile(r"[^\s/]+\.([^\s/.]{2,})")
POTENTIAL_IP_REGEX = re.compile(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}")

User: models.Model = get_user_model()


def paginate(request, queryset, per_page=20, paginator_cls=paginator.Paginator, **kwargs):
    """Get a Paginator, abstracting some common paging actions."""
    p = paginator_cls(queryset, per_page, **kwargs)

    # Get the page from the request, make sure it's an int.
    try:
        page = int(request.GET.get("page", 1))
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
    page = p.page(request.GET.get("page", 1))
    page.url = build_paged_url(request)

    return page


def build_paged_url(request):
    """Build the url for the paginator."""
    base = request.build_absolute_uri(request.path)

    items = [(k, v) for k in request.GET if k != "page" for v in request.GET.getlist(k) if v]

    qsa = urlencode(items)

    return "%s?%s" % (base, qsa)


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
    for i in range(0, length, n):
        yield seq[i : i + n]


def smart_int(string, fallback=0):
    """Convert a string to int, with fallback for invalid strings or types."""
    try:
        return int(float(string))
    except (ValueError, TypeError, OverflowError):
        return fallback


def delete_files_for_obj(sender, instance, **kwargs):
    """Signal receiver of a model class and instance. Deletes its files."""
    for field in sender._meta.get_fields():
        # Check if it's a FileField instance and the field is set.
        if isinstance(field, models.FileField):
            field_file = getattr(instance, field.name)
            if field_file:
                field_file.delete()


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
    if "next" in request.POST:
        url = request.POST.get("next")
    elif "next" in request.GET:
        url = request.GET.get("next")
    else:
        url = request.META.get("HTTP_REFERER")

    if not url:
        return None

    try:
        url_info = urlparse(url)
    except ValueError:
        return None

    if url_info.scheme and url_info.scheme not in {"http", "https"}:
        return None

    if not settings.DEBUG and not url_has_allowed_host_and_scheme(
        url, allowed_hosts={Site.objects.get_current().domain}
    ):
        return None

    return iri_to_uri(url)


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
        raise TruncationException("Can't truncate enough to satisfy " "`max_length`.")
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
        self.estimated = "?"

    def tick(self, incr=1):
        """Advance the current progress, and redraw the screen.

        :param incr: Raise the current progress by this amount. Default: 1
        """
        self.current += incr

        if self.current and self.current % self.milestone_stride == 0:
            now = datetime.now()
            duration = now - self.milestone_time
            duration = duration.seconds + duration.microseconds // 1e6
            rate = self.milestone_stride // duration
            remaining = self.total - self.current
            self.estimated = int(remaining // rate // 60)
            self.milestone_time = now

        self.draw()

    def draw(self):
        """Just redraw the screen."""
        self._wr("{0.current}/{0.total} (Est. {0.estimated} min. remaining)\r".format(self))

    def _wr(self, s):
        sys.stdout.write(s)
        sys.stdout.flush()


def is_ratelimited(request, name, rate, method="POST"):
    """
    Wraps ``ratelimit.core.is_ratelimited`` with sumo-specific details:

    * Always check for the bypass rate limit permission.
    * Log times when users are rate limited.
    * Always uses ``user_or_ip`` for the rate limit key.
    * Adds the Boolean attribute "limited" to the request.
    """
    if request.user.has_perm("sumo.bypass_ratelimit"):
        request.limited = False
        return False

    if limited := is_ratelimited_core(
        request, group=name, key="user_or_ip", rate=rate, method=method, increment=True
    ):
        # We only record a ratelimit event for this counter.
        if request.user.is_authenticated:
            key = f"user '{request.user.username}'"
        else:
            key = f"anonymous user {request.META['REMOTE_ADDR']}"
        Record.objects.info(
            "sumo.ratelimit", "{key} hit the rate limit for {name}", key=key, name=name
        )

    # If the request was already limited, keep it that way.
    request.limited = getattr(request, "limited", False) or limited

    return request.limited


def get_browser(user_agent):
    """Get Browser Name from User Agent"""

    match = re.search(r"(?i)(firefox|msie|chrome|safari|trident)", user_agent, re.IGNORECASE)
    if match:
        browser = match.group(1)
    else:
        browser = None
    return browser


def has_blocked_link(data):
    # TODO: deal with punycode when presented in non-ascii form
    for match in POTENTIAL_LINK_REGEX.finditer(data):
        tld = match.group(1).upper()
        if tld in VALID_TLDS:
            full_domain = match.group(0).lower()
            in_allowlist = False
            for allowed_domain in settings.ALLOW_LINKS_FROM:
                split = full_domain.rsplit(allowed_domain, 1)
                if len(split) != 2 or split[-1]:
                    # allowed_domain isn't in full_domain, or something went wrong
                    # or allowed_domain isn't at the end of full_domain
                    continue
                if not split[0] or split[0][-1] == ".":
                    # allowed_domain equals full_domain
                    # or allowed_domain is a subdomain of full_domain
                    in_allowlist = True
                    break
            if not in_allowlist:
                return True
    for match in POTENTIAL_IP_REGEX.findall(data):
        valid_ip = True
        for part in match.split("."):
            if int(part) > 255:
                valid_ip = False
                break
        if valid_ip:
            return True
    return False


@timeout(seconds=settings.REGEX_TIMEOUT, use_signals=False)
def match_regex_with_timeout(compiled_regex, data):
    """Matches the specified regex.

    Adds a timeout to avoid catastrophic backtracking.
    """
    return any(compiled_regex.findall(data))


def check_for_spam_content(data):
    """Check for spam content in a given text.

    Currently checks for:
    - Toll free numbers
    - Vanity toll free numbers
    - Links in the text.
    """

    # keep only the digits in text
    digits = "".join(filter(type(data).isdigit, data))
    is_toll_free = settings.TOLL_FREE_REGEX.match(digits)

    is_nanp_number = match_regex_with_timeout(settings.NANP_REGEX, data)

    has_links = has_blocked_link(data)

    return is_toll_free or is_nanp_number or has_links


@lru_cache(maxsize=settings.WEBPACK_LRU_CACHE)
def webpack_static(source_path):
    """
    Get the URL for an asset processed by webpack.
    Takes a shortened path to the source, like "sumo/img/mozilla-support.svg"
    """

    with open("./dist/source-to-asset.json") as f:
        source_to_asset = json.load(f)
        try:
            asset = source_to_asset[source_path]
        except KeyError:
            if settings.DEBUG:
                raise RuntimeError(f"{source_path} doesn't exist in webpack bundle")
            return ""
        url = static(asset)
        return url


def is_trusted_user(user: User) -> bool:
    """Given a user ID, checks for group membership.

    If a user belongs to one of the trusted groups as defined in the project
    settings, then is considered a trusted user.
    """
    if not user or not user.is_authenticated:
        return False
    return any(
        [
            user.groups.filter(name__in=settings.TRUSTED_GROUPS).exists(),
            user.is_superuser,
            user.is_staff,
        ]
    )
