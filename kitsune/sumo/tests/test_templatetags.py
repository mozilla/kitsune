# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime

from django.forms.fields import CharField
from django.test.client import RequestFactory

import jinja2
from babel.dates import format_date, format_time, format_datetime
from nose.tools import eq_, assert_raises
from pyquery import PyQuery as pq
from pytz import timezone

from kitsune.sumo.templatetags.jinja_helpers import (
    datetimeformat, DateTimeFormatError, collapse_linebreaks, url, json,
    timesince, label_with_help, static, urlparams, yesno, number,
    remove, f, fe, class_selected)
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


class TestHelpers(TestCase):

    def test_urlparams_unicode(self):
        context = {'q': u'Français'}
        eq_(u'/foo?q=Fran%C3%A7ais', urlparams('/foo', **context))
        context['q'] = u'\u0125help'
        eq_(u'/foo?q=%C4%A5help', urlparams('/foo', **context))

    def test_urlparams_valid(self):
        context = {'a': 'foo', 'b': 'bar'}
        eq_(u'/foo?a=foo&b=bar', urlparams('/foo', **context))

    def test_urlparams_query_string(self):
        eq_(u'/foo?a=foo&b=bar', urlparams('/foo?a=foo', b='bar'))

    def test_urlparams_multivalue(self):
        eq_(u'/foo?a=foo&a=bar', urlparams('/foo?a=foo&a=bar'))
        eq_(u'/foo?a=bar', urlparams('/foo?a=foo', a='bar'))

    def test_urlparams_none(self):
        """Assert a value of None doesn't make it into the query string."""
        eq_(u'/foo', urlparams('/foo', bar=None))

    def test_collapse_linebreaks(self):
        """Make sure collapse_linebreaks works on some tricky cases."""
        eq_(collapse_linebreaks('\r\n \t  \n\r  Trouble\r\n\r\nshooting \r\n'),
            '\r\n  Trouble\r\nshooting\r\n')
        eq_(collapse_linebreaks('Application Basics\n      \n\n      \n      '
                                '\n\n\n        \n          \n            \n   '
                                '           Name'),
            'Application Basics\r\n              Name')

    def test_label_with_help(self):
        field = CharField(label='Foo', help_text='Foo bar')
        field.auto_id = 'foo'
        expect = '<label for="foo" title="Foo bar">Foo</label>'
        eq_(expect, label_with_help(field))

    def test_yesno(self):
        eq_('Yes', yesno(True))
        eq_('No', yesno(False))
        eq_('Yes', yesno(1))
        eq_('No', yesno(0))

    def test_number(self):
        context = {'request': namedtuple('R', 'LANGUAGE_CODE')('en-US')}
        eq_('5,000', number(context, 5000))
        eq_('', number(context, None))

    def test_remove_in_list(self):
        tags = ['tag1', 'tag2']
        tag = 'tag3'
        tags.append(tag)
        tags = remove(tags, tag)
        eq_(2, len(tags))
        assert tag not in tags

    def test_remove_not_in_list(self):
        tags = ['tag1', 'tag2']
        tag = 'tag3'
        tags = remove(tags, tag)
        # Nothing was removed and we didn't crash.
        eq_(2, len(tags))

    def test_static_failure(self):
        """Should not raise an error if the static file is missing."""
        assert static('does/not/exist.js') == ''


class TestDateTimeFormat(TestCase):

    def setUp(self):
        self.timezone = timezone('US/Pacific')
        self.locale = 'en_US'
        url_ = reverse('forums.threads', args=['testslug'])
        self.context = {'request': RequestFactory().get(url_)}
        self.context['request'].LANGUAGE_CODE = self.locale
        self.context['request'].session = {'timezone': self.timezone}

    def _get_datetime_result(self, locale, timezone, format='short',
                             return_format='shortdatetime'):
        value = datetime.fromordinal(733900)
        value = self.timezone.localize(value)
        value_test = value.astimezone(self.timezone)

        value_localize = value_test.astimezone(timezone)
        value_expected = format_datetime(value_localize, format=format,
                                         locale=locale, tzinfo=timezone)
        value_returned = datetimeformat(self.context, value_test,
                                        format=return_format)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_today(self):
        """Expects shortdatetime, format: Today at {time}."""
        date_today = datetime.today()
        date_localize = self.timezone.localize(date_today)
        value_returned = unicode(datetimeformat(self.context, date_today))
        value_expected = 'Today at %s' % format_time(date_localize,
                                                     format='short',
                                                     locale=self.locale,
                                                     tzinfo=self.timezone)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_locale(self):
        """Expects shortdatetime in French."""
        self.context['request'].LANGUAGE_CODE = 'fr'
        self._get_datetime_result('fr', self.timezone)

    def test_default(self):
        """Expects shortdatetime."""
        self._get_datetime_result(self.locale, self.timezone)

    def test_longdatetime(self):
        """Expects long format."""
        self._get_datetime_result(self.locale, self.timezone, 'long',
                                  'longdatetime')

    def test_date(self):
        """Expects date format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_date(value_test, locale=self.locale)
        value_returned = datetimeformat(self.context, value_test, format='date')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_time(self):
        """Expects time format."""
        value_test = datetime.fromordinal(733900)
        value_localize = self.timezone.localize(value_test)
        value_expected = format_time(value_localize, locale=self.locale,
                                     tzinfo=self.timezone)
        value_returned = datetimeformat(self.context, value_test,
                                        format='time')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_datetime(self):
        """Expects datetime format."""
        self._get_datetime_result(self.locale, self.timezone,
                                  'medium', 'datetime')

    def test_year(self):
        """Expects year format."""
        self._get_datetime_result(self.locale, self.timezone,
                                  'yyyy', 'year')

    def test_unknown_format(self):
        """Unknown format raises DateTimeFormatError."""
        date_today = datetime.today()
        assert_raises(DateTimeFormatError, datetimeformat, self.context,
                      date_today, format='unknown')

    def test_timezone(self):
        """Expects Europe/Paris timezone."""
        fr_timezone = timezone('Europe/Paris')
        self.context['request'].LANGUAGE_CODE = 'fr'
        self.context['request'].session = {'timezone': fr_timezone}
        self._get_datetime_result('fr', fr_timezone,
                                  'medium', 'datetime')

    def test_timezone_different_locale(self):
        """Expects Europe/Paris timezone with different locale."""
        fr_timezone = timezone('Europe/Paris')
        self.context['request'].LANGUAGE_CODE = 'tr'
        self.context['request'].session = {'timezone': fr_timezone}
        self._get_datetime_result('tr', fr_timezone,
                                  'medium', 'datetime')

    def test_invalid_value(self):
        """Passing invalid value raises ValueError."""
        assert_raises(ValueError, datetimeformat, self.context, 'invalid')

    def test_json_helper(self):
        eq_('false', json(False))
        eq_('{"foo": "bar"}', json({'foo': 'bar'}))


class TestUrlHelper(TestCase):
    """Tests for the url helper."""

    def test_with_locale(self):
        """Passing a locale to url creates a URL for that locale."""
        u = url('jsi18n', locale='es')
        eq_(u'/es/jsi18n/', u)


class TimesinceTests(TestCase):
    """Tests for the timesince filter"""

    def test_none(self):
        """If None is passed in, timesince returns ''."""
        eq_('', timesince(None))

    def test_trunc(self):
        """Assert it returns only the most significant time division."""
        eq_('1 year ago',
            timesince(datetime(2000, 1, 2), now=datetime(2001, 2, 3)))

    def test_future(self):
        """Test behavior when date is in the future and also when omitting the
        `now` kwarg."""
        eq_('', timesince(datetime(9999, 1, 2)))


class TestFormat(TestCase):
    """Test the |f and |fe filters"""

    def test_f_handles_unicode_in_ascii_strings(self):
        var = u'Pśetergnuś'
        # Note that the format string is not a unicode string.
        eq_(f('{0}', var), var)

    def test_fe_handles_unicode_in_ascii_strings(self):
        var = u'Pśetergnuś'
        # Note that the format string is not a unicode string.
        eq_(fe('{0}', var), var)


class TestClassSelected(TestCase):
    """Test class_selected"""

    def test_is_escaped(self):
        value_returned = class_selected(1, 1)
        type_expected = jinja2.Markup
        eq_(type(value_returned), type_expected)

    def test_is_selected(self):
        value_returned = class_selected(1, 1)
        value_expected = 'class="selected"'
        eq_(value_returned, value_expected)

    def test_is_not_selected(self):
        value_returned = class_selected(0, 1)
        value_expected = ''
        eq_(value_returned, value_expected)
