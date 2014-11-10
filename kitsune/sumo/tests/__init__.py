import re
from functools import wraps
from os import listdir
from os.path import join, dirname
from smtplib import SMTPRecipientsRefused

from django.conf import settings
from django.test import LiveServerTestCase
from django.test.client import Client
from django.test.utils import override_settings

import django_nose
from nose import SkipTest
from nose.tools import eq_
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox import firefox_binary
from test_utils import TestCase as OriginalTestCase

from kitsune import sumo
from kitsune.sumo.urlresolvers import reverse, split_path


def get(client, url, **kwargs):
    return client.get(reverse(url, **kwargs), follow=True)


def post(client, url, data={}, **kwargs):
    return client.post(reverse(url, **kwargs), data, follow=True)


class TestSuiteRunner(django_nose.NoseTestSuiteRunner):
    """This is a test runner that pulls in settings_test.py."""
    def setup_test_environment(self, **kwargs):
        # If we have a settings_test.py let's roll it into our settings.
        try:
            from kitsune import settings_test
            # Use setattr to update Django's proxies:
            for k in dir(settings_test):
                setattr(settings, k, getattr(settings_test, k))
        except ImportError:
            pass
        super(TestSuiteRunner, self).setup_test_environment(**kwargs)


@override_settings(ES_LIVE_INDEX=False)
class TestCase(OriginalTestCase):
    """A modification of ``test_utils.TestCase`` that skips live indexing."""
    pass


def attrs_eq(received, **expected):
    """Compares received's attributes with expected's kwargs."""
    for k, v in expected.iteritems():
        eq_(v, getattr(received, k))


def starts_with(text, substring):
    """Assert `text` starts with `substring`."""
    assert text.startswith(substring), "%r doesn't start with %r" % (text,
                                                                     substring)


def send_mail_raise_smtp(messages):
    """Patch email_utils.send_messages with this in your tests to check what
    happens when an email fails to send."""
    raise SMTPRecipientsRefused(recipients=messages[0].recipients())


def emailmessage_raise_smtp():
    raise SMTPRecipientsRefused(recipients=[])


class LocalizingClient(Client):
    """Client which prepends a locale so test requests can get through
    LocaleURLMiddleware without resulting in a locale-prefix-adding 301.

    Otherwise, we'd have to hard-code locales into our tests everywhere or
    {mock out reverse() and make LocaleURLMiddleware not fire}.

    """
    def request(self, **request):
        """Make a request, but prepend a locale if there isn't one already."""
        # Fall back to defaults as in the superclass's implementation:
        path = request.get('PATH_INFO', self.defaults.get('PATH_INFO', '/'))
        locale, shortened = split_path(path)
        if not locale:
            request['PATH_INFO'] = '/%s/%s' % (settings.LANGUAGE_CODE,
                                               shortened)
        return super(LocalizingClient, self).request(**request)

    # If you use this, you might also find the force_locale=True argument to
    # sumo.urlresolvers.reverse() handy, in case you need to force locale
    # prepending in a one-off case or do it outside a mock request.


class MigrationTests(TestCase):
    """Sanity checks for the SQL migration scripts"""

    @staticmethod
    def _migrations_path():
        """Return the absolute path to the migration script folder."""
        return join(dirname(dirname(dirname(sumo.__file__))), 'migrations')

    def test_unique(self):
        """Assert that the numeric prefixes of the DB migrations are unique."""
        leading_digits = re.compile(r'^\d+')
        seen_numbers = set()
        path = self._migrations_path()
        for filename in listdir(path):
            match = leading_digits.match(filename)
            if match:
                number = match.group()
                if number in seen_numbers:
                    self.fail('There is more than one migration #%s in %s.' %
                              (number, path))
                seen_numbers.add(number)

    def test_innodb_and_utf8(self):
        """Make sure each created table uses the InnoDB engine and UTF-8."""
        # Heuristic: make sure there are at least as many "ENGINE=InnoDB"s as
        # "CREATE TABLE"s. (There might be additional "InnoDB"s in ALTER TABLE
        # statements, which are fine.)
        path = self._migrations_path()
        for filename in sorted(listdir(path)):
            with open(join(path, filename)) as f:
                contents = f.read()
            # Skip migrations that have special comment 'SKIP MIGRATION TESTS'
            if 'SKIP MIGRATION TESTS' in contents:
                continue
            creates = contents.count('CREATE TABLE')
            engines = contents.count('ENGINE=InnoDB')
            encodings = (contents.count('CHARSET=utf8') +
                         contents.count('CHARACTER SET utf8'))
            assert engines >= creates, (
                "There weren't as many occurrences of 'ENGINE=InnoDB' as "
                "of 'CREATE TABLE' in migration %s." % filename)
            assert encodings >= creates, (
                "There weren't as many UTF-8 declarations as"
                "'CREATE TABLE' occurrences in migration %s." % filename)


class MobileTestCase(TestCase):
    def setUp(self):
        super(MobileTestCase, self).setUp()
        self.client.cookies[settings.MOBILE_COOKIE] = 'on'


class SeleniumTestCase(LiveServerTestCase):

    skipme = False

    @classmethod
    def setUpClass(cls):
        try:
            firefox_path = getattr(settings, 'SELENIUM_FIREFOX_PATH', None)
            if firefox_path:
                firefox_bin = firefox_binary.FirefoxBinary(
                    firefox_path=firefox_path)
                kwargs = {'firefox_binary': firefox_bin}
            else:
                kwargs = {}
            cls.webdriver = webdriver.Firefox(**kwargs)
        except (RuntimeError, WebDriverException):
            cls.skipme = True

        super(SeleniumTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if not cls.skipme:
            try:
                cls.webdriver.quit()
            except OSError:
                # For some reason, sometimes the process may not be
                # running at this point.
                pass
        super(SeleniumTestCase, cls).tearDownClass()

    def setUp(self):
        # Don't run if Selenium isn't available
        if self.skipme:
            raise SkipTest('Selenium unavailable.')

        # Go to an empty page before every test
        self.webdriver.get('')


def with_save(func):
    """Decorate a model maker to add a `save` kwarg.

    If save=True, the model maker will save the object before returning it.

    """
    @wraps(func)
    def saving_func(*args, **kwargs):
        save = kwargs.pop('save', False)
        ret = func(*args, **kwargs)
        if save:
            ret.save()
        return ret

    return saving_func


def eq_msg(a, b, msg=None):
    """Shorthand for 'assert a == b, "%s %r != %r" % (msg, a, b)'
    """
    assert a == b, (str(msg) or '') + ' (%r != %r)' % (a, b)
