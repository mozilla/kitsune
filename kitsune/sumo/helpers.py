import datetime
import json as jsonlib
import re
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse as django_reverse
from django.http import QueryDict
from django.utils.encoding import smart_str
from django.utils.http import urlencode
from django.utils.tzinfo import LocalTimezone

import bleach
import jinja2
from babel import localedata
from babel.dates import format_date, format_time, format_datetime
from babel.numbers import format_decimal
from jingo import register, env
from jinja2.utils import Markup
from pytz import timezone
from tower import ugettext_lazy as _lazy, ugettext as _, ungettext

from kitsune.sumo import parser
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import Profile
from kitsune.wiki.showfor import showfor_data as _showfor_data


class DateTimeFormatError(Exception):
    """Called by the datetimeformat function when receiving invalid format."""
    pass


@register.filter
def paginator(pager):
    """Render list of pages."""
    return Paginator(pager).render()


@register.filter
def simple_paginator(pager):
    t = env.get_template('includes/simple_paginator.html')
    return jinja2.Markup(t.render({'pager': pager}))


@register.filter
def quick_paginator(pager):
    t = env.get_template('includes/quick_paginator.html')
    return jinja2.Markup(t.render({'pager': pager}))


@register.filter
def mobile_paginator(pager):
    t = env.get_template('includes/mobile/paginator.html')
    return jinja2.Markup(t.render({'pager': pager}))


@register.function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates.

    Uses sumo's locale-aware reverse."""
    locale = kwargs.pop('locale', None)
    return reverse(viewname, locale=locale, args=args, kwargs=kwargs)


@register.function
def unlocalized_url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates.

    Uses django's default reverse."""
    return django_reverse(viewname, args=args, kwargs=kwargs)


@register.filter
def urlparams(url_, hash=None, query_dict=None, **query):
    """
    Add a fragment and/or query parameters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url_ = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url_.fragment

    q = url_.query
    new_query_dict = (QueryDict(smart_str(q), mutable=True) if
                      q else QueryDict('', mutable=True))
    if query_dict:
        for k, l in query_dict.lists():
            new_query_dict[k] = None  # Replace, don't append.
            for v in l:
                new_query_dict.appendlist(k, v)

    for k, v in query.items():
        new_query_dict[k] = v  # Replace, don't append.

    query_string = urlencode([(k, v) for k, l in new_query_dict.lists() for
                              v in l if v is not None])
    new = urlparse.ParseResult(url_.scheme, url_.netloc, url_.path,
                               url_.params, query_string, fragment)
    return new.geturl()


@register.filter
def wiki_to_html(wiki_markup, locale=settings.WIKI_DEFAULT_LANGUAGE,
                 nofollow=True):
    """Wiki Markup -> HTML jinja2.Markup object"""
    return jinja2.Markup(parser.wiki_to_html(wiki_markup, locale=locale,
                                             nofollow=nofollow))


@register.filter
def truncate_question(text, length, longtext=None):
    if len(text) > length:
        if longtext is None:
            longtext = text
        stripped_text = bleach.clean(text, tags=[], strip=True)

        f = ('<p class="short-text">%s&hellip; ' +
             '<span class="show-more-link">(' + _('read more') + ')</span>' +
             '</p><div class="long-text">%s</div>')
        return f % (stripped_text[:length], longtext)

    return text


class Paginator(object):

    def __init__(self, pager):
        self.pager = pager

        self.max = 10
        self.span = (self.max - 1) / 2

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
        return range(max(lower + 1, 1), min(total, upper) + 1)

    def render(self):
        c = {'pager': self.pager, 'num_pages': self.num_pages,
             'count': self.count}
        t = env.get_template('layout/paginator.html').render(c)
        return jinja2.Markup(t)


@register.function
@jinja2.contextfunction
def breadcrumbs(context, items=list(), add_default=True, id=None):
    """
    Show a list of breadcrumbs. If url is None, it won't be a link.
    Accepts: [(url, label)]
    """
    if add_default:
        first_crumb = u'Home'

        crumbs = [(reverse('home'), _lazy(first_crumb))]
    else:
        crumbs = []

    # add user-defined breadcrumbs
    if items:
        try:
            crumbs += items
        except TypeError:
            crumbs.append(items)

    c = {'breadcrumbs': crumbs, 'id': id}

    t = env.get_template('layout/breadcrumbs.html').render(c)
    return jinja2.Markup(t)


def _babel_locale(locale):
    """Return the Babel locale code, given a normal one."""
    # Babel uses underscore as separator.
    return locale.replace('-', '_')


def _contextual_locale(context):
    """Return locale from the context, falling back to a default if invalid."""
    request = context.get('request')
    locale = request.LANGUAGE_CODE
    if not localedata.exists(locale):
        locale = settings.LANGUAGE_CODE
    return locale


@register.function
@jinja2.contextfunction
def datetimeformat(context, value, format='shortdatetime'):
    """
    Returns a formatted date/time using Babel's locale settings. Uses the
    timezone from settings.py, if the user has not been authenticated.
    """
    if not isinstance(value, datetime.datetime):
        # Expecting date value
        raise ValueError(
            'Unexpected value {value} passed to datetimeformat'.format(
                value=value))

    request = context.get('request')

    default_tzinfo = convert_tzinfo = timezone(settings.TIME_ZONE)
    if value.tzinfo is None:
        value = default_tzinfo.localize(value)
        new_value = value.astimezone(default_tzinfo)
    else:
        new_value = value

    if 'timezone' not in request.session:
        if request.user.is_authenticated():
            try:
                convert_tzinfo = (Profile.objects.get(user=request.user).timezone or
                                  default_tzinfo)
            except (Profile.DoesNotExist, AttributeError):
                pass
        request.session['timezone'] = convert_tzinfo
    else:
        convert_tzinfo = request.session['timezone']

    convert_value = new_value.astimezone(convert_tzinfo)
    locale = _babel_locale(_contextual_locale(context))

    # If within a day, 24 * 60 * 60 = 86400s
    if format == 'shortdatetime':
        # Check if the date is today
        today = datetime.datetime.now(tz=convert_tzinfo).toordinal()
        if convert_value.toordinal() == today:
            formatted = _lazy(u'Today at %s') % format_time(
                convert_value, format='short', tzinfo=convert_tzinfo,
                locale=locale)
        else:
            formatted = format_datetime(convert_value,
                                        format='short',
                                        tzinfo=convert_tzinfo,
                                        locale=locale)
    elif format == 'longdatetime':
        formatted = format_datetime(convert_value, format='long',
                                    tzinfo=convert_tzinfo, locale=locale)
    elif format == 'date':
        formatted = format_date(convert_value, locale=locale)
    elif format == 'time':
        formatted = format_time(convert_value, tzinfo=convert_tzinfo,
                                locale=locale)
    elif format == 'datetime':
        formatted = format_datetime(convert_value, tzinfo=convert_tzinfo,
                                    locale=locale)
    else:
        # Unknown format
        raise DateTimeFormatError

    return jinja2.Markup('<time datetime="%s">%s</time>' %
                         (convert_value.isoformat(), formatted))


_whitespace_then_break = re.compile(r'[\r\n\t ]+[\r\n]+')


@register.filter
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
    return _whitespace_then_break.sub('\r\n', text)


@register.filter
def json(s):
    return jsonlib.dumps(s)


@register.function
@jinja2.contextfunction
def number(context, n):
    """Return the localized representation of an integer or decimal.

    For None, print nothing.

    """
    if n is None:
        return ''
    return format_decimal(n, locale=_babel_locale(_contextual_locale(context)))


@register.filter
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
        return u''
    chunks = [
        (60 * 60 * 24 * 365, lambda n: ungettext('%(number)d year ago',
                                                 '%(number)d years ago', n)),
        (60 * 60 * 24 * 30, lambda n: ungettext('%(number)d month ago',
                                                '%(number)d months ago', n)),
        (60 * 60 * 24 * 7, lambda n: ungettext('%(number)d week ago',
                                               '%(number)d weeks ago', n)),
        (60 * 60 * 24, lambda n: ungettext('%(number)d day ago',
                                           '%(number)d days ago', n)),
        (60 * 60, lambda n: ungettext('%(number)d hour ago',
                                      '%(number)d hours ago', n)),
        (60, lambda n: ungettext('%(number)d minute ago',
                                 '%(number)d minutes ago', n)),
        (1, lambda n: ungettext('%(number)d second ago',
                                '%(number)d seconds ago', n))]
    if not now:
        if d.tzinfo:
            now = datetime.datetime.now(LocalTimezone(d))
        else:
            now = datetime.datetime.now()

    # Ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return u''
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    return name(count) % {'number': count}


@register.filter
def label_with_help(f):
    """Print the label tag for a form field, including the help_text
    value as a title attribute."""
    label = u'<label for="%s" title="%s">%s</label>'
    return jinja2.Markup(label % (f.auto_id, f.help_text, f.label))


@register.filter
def yesno(boolean_value):
    return jinja2.Markup(_lazy(u'Yes') if boolean_value else _lazy(u'No'))


@register.filter
def remove(list_, item):
    """Removes an item from a list."""
    return [i for i in list_ if i != item]


@register.function
@jinja2.contextfunction
def ga_push_attribute(context):
    """Return the json for the data-ga-push attribute.

    This is used to defined custom variables and other special tracking with
    Google Analytics.
    """
    request = context.get('request')
    ga_push = context.get('ga_push', [])

    # If the user is on the first page after logging in,
    # we add a "User Type" custom variable.
    if request.GET.get('fpa') == '1' and request.user.is_authenticated():
        user = request.user
        group_names = user.groups.values_list('name', flat=True)

        # If they belong to the Administrator group:
        if 'Administrators' in group_names:
            ga_push.append(
                ['_setCustomVar', 1, 'User Type', 'Contributor - Admin', 1])
        # If they belong to the Contributors group:
        elif 'Contributors' in group_names:
            ga_push.append(['_setCustomVar', 1, 'User Type', 'Contributor', 1])
        # If they don't belong to any of these groups:
        else:
            ga_push.append(['_setCustomVar', 1, 'User Type', 'Registered', 1])

    return jsonlib.dumps(ga_push)


@register.function
@jinja2.contextfunction
def is_secure(context):
    request = context.get('request')
    if request and hasattr(request, 'is_secure'):
        return context.get('request').is_secure()

    return False


@register.filter
def linkify(text):
    return bleach.linkify(text)


@register.function
def showfor_data(products):
    # Markup() marks this data as safe.
    return Markup(jsonlib.dumps(_showfor_data(products)))


@register.function
def add_utm(url_, campaign, source='notification', medium='email'):
    """Add the utm_* tracking parameters to a URL."""
    return urlparams(
        url_, utm_campaign=campaign, utm_source=source, utm_medium=medium)


@register.function
def to_unicode(str):
    return unicode(str)
