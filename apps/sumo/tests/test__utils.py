# -*- coding: utf8 -*-
import json
from mock import patch
from nose.tools import eq_
from test_utils import RequestFactory

from sumo.utils import smart_int, get_next_url, truncated_json_dumps
from sumo.tests import TestCase


class SmartIntTestCase(TestCase):
    def test_sanity(self):
        eq_(10, smart_int('10'))
        eq_(10, smart_int('10.5'))

    def test_int(self):
        eq_(10, smart_int(10))

    def test_invalid_string(self):
        eq_(0, smart_int('invalid'))

    def test_empty_string(self):
        eq_(0, smart_int(''))

    def test_wrong_type(self):
        eq_(0, smart_int(None))
        eq_(10, smart_int([], 10))

    def test_large_values(self):
        """Makes sure ints that would cause an overflow result in fallback."""
        eq_(0, smart_int('1' * 1000))


class GetNextUrlTests(TestCase):
    def setUp(self):
        super(GetNextUrlTests, self).setUp()
        self.r = RequestFactory()
        self.patcher = patch('django.contrib.sites.models.Site.objects')
        mock = self.patcher.start()
        mock.get_current.return_value.domain = 'su.mo.com'

    def tearDown(self):
        self.patcher.stop()
        super(GetNextUrlTests, self).tearDown()

    def test_https(self):
        """Verify that protocol and domain get removed for https."""
        r = self.r.post('/users/login',
                        {'next': 'https://su.mo.com/kb/new?f=b'})
        eq_('/kb/new?f=b', get_next_url(r))

    def test_http(self):
        """Verify that protocol and domain get removed for http."""
        r = self.r.post('/users/login',
                        {'next': 'http://su.mo.com/kb/new'})
        eq_('/kb/new', get_next_url(r))

class JSONTests(TestCase):
    def test_truncated_noop(self):
        """Make sure short enough things are unmodified."""
        d = {'foo': 'bar'}
        trunc = truncated_json_dumps(d, 1000, 'foo')
        eq_(json.dumps(d), trunc)

    def test_truncated_key(self):
        """Make sure truncation works as expected."""
        d = {'foo': 'a long string that should be truncated'}
        trunc = truncated_json_dumps(d, 30, 'foo')
        obj = json.loads(trunc)
        eq_(obj['foo'], 'a long string that ')
        eq_(len(trunc), 30)

    def test_unicode(self):
        """Unicode should not be treated as longer than it is."""
        d = {'formula': u'A=πr²'}
        trunc = truncated_json_dumps(d, 25, 'formula')
        eq_(json.dumps(d, ensure_ascii=False), trunc)
