# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime

from django.forms.fields import CharField

from babel.dates import format_date, format_time, format_datetime
import jingo
from mock import Mock
from nose.tools import eq_, assert_raises
from pytz import timezone
from pyquery import PyQuery as pq
import test_utils

from sumo.helpers import (datetimeformat, DateTimeFormatError,
                          collapse_linebreaks, url, json, timesince,
                          label_with_help, urlparams, yesno, number, remove)
from sumo.tests import TestCase
from sumo.urlresolvers import reverse

from users.models import RegistrationProfile, Setting


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


class TestHelpers(TestCase):

    def setUp(self):
        jingo.load_helpers()

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
        context = {'request': namedtuple('R', 'locale')('en-US')}
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


class TestDateTimeFormat(TestCase):

    def setUp(self):
        self.timezone = timezone('US/Pacific')
        self.locale = u'en_US'
        url_ = reverse('forums.threads', args=[u'testslug'])
        user = RegistrationProfile.objects.create_inactive_user(
                    'sumouser1234', 'testpass', 'sumouser@test.com',
                    locale=self.locale)
        self.context = {'request': test_utils.RequestFactory().get(url_)}
        self.context['request'].locale = self.locale
        self.context['request'].user = user.profile
        self.context['request'].user.is_authenticated = Mock(return_value=True)
        self.context['request'].session = {'timezone': self.timezone}

    def test_today(self):
        """Expects shortdatetime, format: Today at {time}."""
        date_today = datetime.today()
        value_returned = unicode(datetimeformat(self.context, date_today))
        value_expected = 'Today at %s' % format_time(date_today,
                                                     format='short',
                                                     locale=self.locale,
                                                     tzinfo=self.timezone)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_locale(self):
        """Expects shortdatetime in French."""
        self.context['request'].locale = u'fr'
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format='short',
                                         locale=u'fr', tzinfo=self.timezone)
        value_returned = datetimeformat(self.context, value_test)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_default(self):
        """Expects shortdatetime."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format='short',
                                         locale=self.locale, tzinfo=self.timezone)
        value_returned = datetimeformat(self.context, value_test)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_longdatetime(self):
        """Expects long format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format='long',
                                         locale=self.locale, tzinfo=self.timezone)
        value_returned = datetimeformat(self.context, value_test,
                                        format='longdatetime')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_date(self):
        """Expects date format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_date(value_test, locale=self.locale)
        value_returned = datetimeformat(self.context, value_test,
                                        format='date')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_time(self):
        """Expects time format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_time(value_test, locale=self.locale,
                                     tzinfo=self.timezone)
        value_returned = datetimeformat(self.context, value_test,
                                        format='time')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_datetime(self):
        """Expects datetime format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, locale=self.locale,
                                         tzinfo=self.timezone)
        value_returned = datetimeformat(self.context, value_test,
                                        format='datetime')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_unknown_format(self):
        """Unknown format raises DateTimeFormatError."""
        date_today = datetime.today()
        assert_raises(DateTimeFormatError, datetimeformat, self.context,
                      date_today, format='unknown')

    def test_timezone(self):
        self.context['request'].locale = u'fr'
        self.context['request'].session = {'timezone': timezone('Europe/Paris')}
        date = datetime(2007, 04, 01, 15, 30)
        value_expected = format_datetime(date, tzinfo=self.timezone,
                        locale=u'fr')
        value_returned = datetimeformat(self.context, date,
                                                format='datetime')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_timezone_different_locale(self):
        locale = u'tr'
        formats = ['full', 'long', 'medium', 'short']
        results = [u'01 Nisan 2007 Pazar 17:30:00 Fransa Saati',
                   u'1 Nisan 2007 17:30:00 +0200', u'01.Nis.2007 17:30:00',
                   u'01.04.2007 17:30']
        date = datetime(2007, 04, 01, 15, 30)
        for format, result in zip(formats, results):
            value_expected = format_datetime(date, format,
                                             tzinfo=timezone('Europe/Paris'),
                                             locale=locale)
            eq_(value_expected, result)

    def test_same_timezone(self):
        date = datetime(2007, 04, 01, 15, 30)
        value_expected = format_datetime(date, 'long', tzinfo=self.timezone,
                        locale=self.locale)
        eq_(value_expected, u'April 1, 2007 8:30:00 AM PDT')

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
