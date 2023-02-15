import datetime
import json as jsonlib
import logging
import re
import urllib
from zoneinfo import ZoneInfo

import bleach
import jinja2
from babel import localedata
from babel.dates import format_date, format_datetime, format_time
from babel.numbers import format_decimal
from django.conf import settings
from django.http import QueryDict
from django.template.loader import render_to_string
from django.templatetags.static import static as django_static
from django.utils.encoding import smart_bytes, smart_str
from django.utils.http import urlencode
from django.utils.timezone import get_default_timezone, is_aware, is_naive
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import ngettext
from django_jinja import library
from markupsafe import Markup, escape

from kitsune.products.models import Product
from kitsune.sumo import parser
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import is_trusted_user as is_trusted_user_func
from kitsune.sumo.utils import webpack_static as webpack_static_func
from kitsune.users.models import Profile
from kitsune.wiki.showfor import showfor_data as _showfor_data

ALLOWED_BIO_TAGS = bleach.ALLOWED_TAGS | {"p"}
ALLOWED_BIO_ATTRIBUTES = bleach.ALLOWED_ATTRIBUTES.copy()
# allow rel="nofollow"
ALLOWED_BIO_ATTRIBUTES["a"].append("rel")
log = logging.getLogger("k.helpers")


class DateTimeFormatError(Exception):
    """Called by the datetimeformat function when receiving invalid format."""

    pass


@library.filter
def paginator(pager):
    """Render list of pages."""
    return Paginator(pager).render()


@library.filter
def simple_paginator(pager):
    return Markup(render_to_string("includes/simple_paginator.html", {"pager": pager}))


@library.filter
def quick_paginator(pager):
    return Markup(render_to_string("includes/quick_paginator.html", {"pager": pager}))


@library.filter
def mobile_paginator(pager):
    return Markup(render_to_string("includes/mobile/paginator.html", {"pager": pager}))


@library.global_function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates.

    Uses sumo's locale-aware reverse."""
    locale = kwargs.pop("locale", None)
    return reverse(viewname, locale=locale, args=args, kwargs=kwargs)


@library.global_function
def canonicalize(viewname=None, model_url=None, *args, **kwargs):
    suffix = model_url if model_url else reverse(viewname, args=args, kwargs=kwargs)
    return "{}{}".format(settings.CANONICAL_URL, suffix)


@library.filter
def urlparams(url_, hash=None, query_dict=None, **query):
    """
    Add a fragment and/or query parameters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url_ = urllib.parse.urlparse(url_)
    fragment = hash if hash is not None else url_.fragment

    q = url_.query
    new_query_dict = QueryDict(smart_bytes(q), mutable=True) if q else QueryDict("", mutable=True)
    if query_dict:
        for k, l in query_dict.lists():
            new_query_dict[k] = None  # Replace, don't append.
            for v in l:
                new_query_dict.appendlist(k, v)

    for k, v in list(query.items()):
        new_query_dict[k] = v  # Replace, don't append.

    query_string = urlencode(
        [(k, v) for k, l in new_query_dict.lists() for v in l if v is not None]
    )
    new = urllib.parse.ParseResult(
        url_.scheme, url_.netloc, url_.path, url_.params, query_string, fragment
    )
    return new.geturl()


@library.filter
def wiki_to_html(wiki_markup, locale=settings.WIKI_DEFAULT_LANGUAGE, nofollow=True):
    """Wiki Markup -> HTML Markup object"""
    if not wiki_markup:
        return ""
    return Markup(parser.wiki_to_html(wiki_markup, locale=locale, nofollow=nofollow))


@library.filter
def wiki_to_safe_html(wiki_markup, locale=settings.WIKI_DEFAULT_LANGUAGE, nofollow=True):
    """Wiki Markup -> HTML Markup object with limited tags"""
    html = parser.wiki_to_html(wiki_markup, locale=locale, nofollow=nofollow)
    return Markup(
        bleach.clean(html, tags=ALLOWED_BIO_TAGS, attributes=ALLOWED_BIO_ATTRIBUTES, strip=True)
    )


@library.filter
def truncate_question(text, length, longtext=None):
    if len(text) > length:
        if longtext is None:
            longtext = text
        stripped_text = bleach.clean(text, tags=[], strip=True)

        f = (
            '<p class="short-text">%s&hellip; '
            + '<a href="#" class="show-more-link">('
            + _("read more")
            + ")</a>"
            + '</p><div class="long-text">%s</div>'
        )
        return f % (stripped_text[:length], longtext)

    return text


class Paginator(object):
    def __init__(self, pager):
        self.pager = pager

        self.max = 10
        self.span = (self.max - 1) // 2

        self.page = pager.number
        self.num_pages = pager.paginator.num_pages
        self.count = pager.paginator.count

        pager.page_range = self.range()
        pager.dotted_upper = self.num_pages not in pager.page_range
        pager.dotted_lower = 1 not in pager.page_range

    def range(self):
        """Return a list of page numbers to show in the paginator."""
        page, total, span = self.page, self.num_pages, self.span
        if total < self.max:
            lower, upper = 0, total
        elif page < span + 1:
            lower, upper = 0, span * 2
        elif page > total - span:
            lower, upper = total - span * 2, total
        else:
            lower, upper = page - span, page + span - 1
        return list(range(max(lower + 1, 1), min(total, upper) + 1))

    def render(self):
        c = {"pager": self.pager, "num_pages": self.num_pages, "count": self.count}
        return Markup(render_to_string("layout/paginator.html", c))


@jinja2.pass_context
@library.global_function
def breadcrumbs(context, items=list(), add_default=True, id=None):
    """
    Show a list of breadcrumbs. If url is None, it won't be a link.
    Accepts: [(url, label)]
    """
    if add_default:
        first_crumb = "Home"

        crumbs = [("/", _lazy(first_crumb))]
    else:
        crumbs = []

    # add user-defined breadcrumbs
    if items:
        try:
            crumbs += items
        except TypeError:
            crumbs.append(items)

    c = {"breadcrumbs": crumbs, "id": id}

    return Markup(render_to_string("layout/breadcrumbs.html", c))


def _babel_locale(locale):
    """Return the Babel locale code, given a normal one."""
    # Babel uses underscore as separator.
    return locale.replace("-", "_")


def _contextual_locale(context):
    """Return locale from the context, falling back to a default if invalid."""
    request = context.get("request")
    locale = request.LANGUAGE_CODE
    if not localedata.exists(locale):
        locale = settings.LANGUAGE_CODE
    return locale


@jinja2.pass_context
@library.global_function
def datetimeformat(context, value, format="shortdatetime"):
    """
    Returns a formatted date/time using Babel's locale settings. Uses the
    timezone from settings.py, if the user has not been authenticated.
    """
    if not isinstance(value, datetime.datetime):
        # Expecting date value
        raise ValueError("Unexpected value {value} passed to datetimeformat".format(value=value))

    request = context.get("request")

    default_tzinfo = convert_tzinfo = ZoneInfo(settings.TIME_ZONE)
    if is_naive(value):
        # Since Python 3.9, due to the introduction of the new "fold" parameter, this is the
        # recommended way to convert a datetime instance from "naive" to "aware".
        new_value = value.replace(tzinfo=default_tzinfo)
    else:
        new_value = value

    if hasattr(request, "session"):
        if "timezone" not in request.session:
            if hasattr(request, "user") and request.user.is_authenticated:
                try:
                    convert_tzinfo = (
                        Profile.objects.get(user=request.user).timezone or default_tzinfo
                    )
                except (Profile.DoesNotExist, AttributeError):
                    pass
            request.session["timezone"] = convert_tzinfo
        else:
            convert_tzinfo = request.session["timezone"] or default_tzinfo

    convert_value = new_value.astimezone(convert_tzinfo)
    locale = _babel_locale(_contextual_locale(context))

    # If within a day, 24 * 60 * 60 = 86400s
    if format == "shortdatetime":
        # Check if the date is today
        today = datetime.datetime.now(tz=convert_tzinfo).toordinal()
        if convert_value.toordinal() == today:
            formatted = _lazy("Today at %s") % format_time(
                convert_value, format="short", tzinfo=convert_tzinfo, locale=locale
            )
        else:
            formatted = format_datetime(
                convert_value, format="short", tzinfo=convert_tzinfo, locale=locale
            )
    elif format == "longdatetime":
        formatted = format_datetime(
            convert_value, format="long", tzinfo=convert_tzinfo, locale=locale
        )
    elif format == "date":
        formatted = format_date(convert_value, locale=locale)
    elif format == "time":
        formatted = format_time(convert_value, tzinfo=convert_tzinfo, locale=locale)
    elif format == "datetime":
        formatted = format_datetime(convert_value, tzinfo=convert_tzinfo, locale=locale)
    elif format == "year":
        formatted = format_datetime(
            convert_value, format="yyyy", tzinfo=convert_tzinfo, locale=locale
        )
    else:
        # Unknown format
        raise DateTimeFormatError

    return Markup('<time datetime="%s">%s</time>' % (convert_value.isoformat(), formatted))


_whitespace_then_break = re.compile(r"[\r\n\t ]+[\r\n]+")


@library.filter
def collapse_linebreaks(text):
    """Replace consecutive CRs and/or LFs with single CRLFs.

    CRs or LFs with nothing but whitespace between them are still considered
    consecutive.

    As a nice side effect, also strips trailing whitespace from lines that are
    followed by line breaks.

    """
    # I previously tried an heuristic where we'd cut the number of linebreaks
    # in half until there remained at least one lone linebreak in the text.
    # However, about:support in some versions of Firefox does yield some hard-
    # wrapped paragraphs using single linebreaks.
    return _whitespace_then_break.sub("\r\n", text)


@library.filter
def json(s):
    return jsonlib.dumps(s)


@jinja2.pass_context
@library.global_function
def number(context, n):
    """Return the localized representation of an integer or decimal.

    For None, print nothing.

    """
    if n is None:
        return ""
    return format_decimal(n, locale=_babel_locale(_contextual_locale(context)))


@library.filter
def timesince(d, now=None):
    """Take two datetime objects and return the time between d and now as a
    nicely formatted string, e.g. "10 minutes".  If d is None or occurs after
    now, return ''.

    Units used are years, months, weeks, days, hours, and minutes. Seconds and
    microseconds are ignored.  Just one unit is displayed.  For example,
    "2 weeks" and "1 year" are possible outputs, but "2 weeks, 3 days" and "1
    year, 5 months" are not.

    Adapted from django.utils.timesince to have better i18n (not assuming
    commas as list separators and including "ago" so order of words isn't
    assumed), show only one time unit, and include seconds.

    """
    if d is None:
        return ""
    chunks = [
        (
            60 * 60 * 24 * 365,
            lambda n: ngettext("%(number)d year ago", "%(number)d years ago", n),
        ),
        (
            60 * 60 * 24 * 30,
            lambda n: ngettext("%(number)d month ago", "%(number)d months ago", n),
        ),
        (
            60 * 60 * 24 * 7,
            lambda n: ngettext("%(number)d week ago", "%(number)d weeks ago", n),
        ),
        (
            60 * 60 * 24,
            lambda n: ngettext("%(number)d day ago", "%(number)d days ago", n),
        ),
        (
            60 * 60,
            lambda n: ngettext("%(number)d hour ago", "%(number)d hours ago", n),
        ),
        (60, lambda n: ngettext("%(number)d minute ago", "%(number)d minutes ago", n)),
        (1, lambda n: ngettext("%(number)d second ago", "%(number)d seconds ago", n)),
    ]
    if not now:
        if is_aware(d):
            now = datetime.datetime.now(get_default_timezone())
        else:
            now = datetime.datetime.now()

    # Ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return ""
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    return name(count) % {"number": count}


@library.filter
def label_with_help(f):
    """Print the label tag for a form field, including the help_text
    value as a title attribute."""
    label = '<label for="%s" title="%s">%s</label>'
    return Markup(label % (f.auto_id, f.help_text, f.label))


@library.filter
def yesno(boolean_value):
    return Markup(_lazy("Yes") if boolean_value else _lazy("No"))


@library.filter
def remove(list_, item):
    """Removes an item from a list."""
    return [i for i in list_ if i != item]


@jinja2.pass_context
@library.global_function
def is_secure(context):
    request = context.get("request")
    if request and hasattr(request, "is_secure"):
        return context.get("request").is_secure()

    return False


@library.filter
def linkify(text):
    return bleach.linkify(text)


@library.global_function
def showfor_data(products):
    # Markup() marks this data as safe.
    return Markup(jsonlib.dumps(_showfor_data(products)))


@library.global_function
def add_utm(url_, campaign, source="notification", medium="email"):
    """Add the utm_* tracking parameters to a URL."""
    return urlparams(url_, utm_campaign=campaign, utm_source=source, utm_medium=medium)


@library.global_function
def to_unicode(value):
    return str(value)


@library.global_function
def static(path):
    """Generate a URL for the specified static file."""
    try:
        return django_static(path)
    except ValueError as err:
        log.error("Static helper error: %s" % err)
        return ""


@library.global_function
def webpack_static(source_path):
    return webpack_static_func(source_path)


@library.global_function
def now():
    return datetime.datetime.now()


@library.filter
def class_selected(a, b):
    """
    Return 'class="selected"' if a == b, otherwise return ''.
    """
    if a == b:
        return Markup('class="selected"')
    else:
        return ""


@library.filter
def f(format_string, *args, **kwargs):
    """
    Uses ``str.format`` for string interpolation.

    >>> {{ "{0} arguments and {x} arguments"|f('positional', x='keyword') }}
    "positional arguments and keyword arguments"

    """
    # Jinja will sometimes give us a str and other times give a unicode
    # for the `format_string` parameter, and we can't control it, so coerce it here.
    if isinstance(format_string, str):  # not unicode
        format_string = str(format_string)

    return format_string.format(*args, **kwargs)


@library.filter
def fe(format_string, *args, **kwargs):
    """Format a safe string with potentially unsafe arguments. returns a safe string."""

    args = [escape(smart_str(v)) for v in args]

    for k in kwargs:
        kwargs[k] = escape(smart_str(kwargs[k]))

    # Jinja will sometimes give us a str and other times give a unicode
    # for the `format_string` parameter, and we can't control it, so coerce it here.
    if isinstance(format_string, str):  # not unicode
        format_string = str(format_string)

    return Markup(format_string.format(*args, **kwargs))


@library.global_function
def image_for_product(product_slug):
    """
    Return square/alternate image for product slug
    """
    default_image = webpack_static("products/img/product_placeholder_alternate.png")

    if not product_slug:
        return default_image

    try:
        obj = Product.objects.get(slug=product_slug)
    except Product.DoesNotExist:
        return default_image
    return obj.image_alternate_url


@jinja2.pass_context
@library.global_function
def show_header_fx_download(context):
    """
    Decides whether or not to render the Firefox download button in the header based on the
    current product being displayed.

    If a visitor is on a Firefox product page of any sort - help topics, KB article, etc -
    the header download button should be hidden, because these Firefox product pages all
    display a big download button in page. (We don't want to put multiple download buttons
    on the page.)

    This function is used in conjunction with show-fx-download.js. This function simply adds
    markup to the template wrapped in a 'hidden' class. The JS removes the 'hidden' class if
    the visitor is *NOT* already using Firefox.
    """
    product = context.get("product", None)

    # product is *usually* an instance of Product, but sometimes (during AAQ process) product
    # is a dict (see questions/config.py).
    if product and hasattr(product, "slug"):
        return product.slug != "firefox"
    else:
        return True


@library.global_function
def is_trusted_user(user):
    return is_trusted_user_func(user)
