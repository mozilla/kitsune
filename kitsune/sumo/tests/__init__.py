# -*- coding: utf-8 -*-
import inspect
import os
import sys
from functools import wraps
from os import getenv
from smtplib import SMTPRecipientsRefused

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.test import LiveServerTestCase, TestCase as OriginalTestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils.translation import trans_real

import django_nose
import factory.fuzzy
from nose.tools import eq_
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox import firefox_binary
from waffle.models import Flag

from kitsune.sumo.urlresolvers import reverse, split_path


# We do this gooftastic thing because nose uses unittest.SkipTest in
# Python 2.7 which doesn't work with the whole --no-skip thing.
if '--no-skip' in sys.argv or 'NOSE_WITHOUT_SKIP' in os.environ:
    class SkipTest(Exception):
        pass
else:
    from nose import SkipTest


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

        if not getenv('REUSE_STATIC', 'false').lower() in ('true', '1', ''):
            # Collect static files for pipeline to work correctly
            call_command('collectstatic', interactive=False)

        super(TestSuiteRunner, self).setup_test_environment(**kwargs)


@override_settings(ES_LIVE_INDEX=False)
class TestCase(OriginalTestCase):
    """TestCase that skips live indexing."""
    def _pre_setup(self):
        cache.clear()
        trans_real.deactivate()
        trans_real._translations = {}  # Django fails to clear this cache.
        trans_real.activate(settings.LANGUAGE_CODE)
        super(TestCase, self)._pre_setup()


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


class FuzzyUnicode(factory.fuzzy.FuzzyText):
    """A FuzzyText factory that contains at least one non-ASCII character."""

    def fuzz(self):
        return u'đ{}'.format(super(FuzzyUnicode, self).fuzz())


class set_waffle_flag(object):
    """
    Decorator/context manager that sets a given waffle flag.

    When applied to a function or method, it sets the value of the flag
    before the function is called, and resets the flag to its original
    value afterwards.

    When applies to a class, it decorates every method in the class
    that has a name beginning with "test" with this decorator.

    When used as a context manager, enables the flag before running the
    wrapped code, and resets the flag afterwards.

    Usage::

        @set_waffle_flag('some_flag')
        class TestClass(TestCase):
            def test_the_thing(self):
                ...

        @set_waffle_flag('some_flag', everyone=False)
        def test_my_view():
            ...

        with set_waffle_flag('some_flag', everyone=True):
            ...
    """

    def __init__(self, flagname, **kwargs):
        self.flagname = flagname
        self.kwargs = kwargs or {'everyone': True}

        try:
            self.origflag = Flag.objects.get(name=self.flagname)
            self.origid = self.origflag.id
        except Flag.DoesNotExist:
            self.origflag = None
            self.origid = None

    def __call__(self, func_or_class):
        """Decorate a class or function"""
        if inspect.isclass(func_or_class):
            # If func_or_class is a class, decorate all of its methods
            # that start with 'test'.
            for attr in func_or_class.__dict__.keys():
                prop = getattr(func_or_class, attr)
                if attr.startswith('test') and callable(prop):
                    setattr(func_or_class, attr, self.decorate(prop))
            return func_or_class
        else:
            # If func_or_class is a function, decorate it directly
            return self.decorate(func_or_class)

    def __enter__(self):
        """Start acting like a context manager."""
        self.make_flag()

    def __exit__(self, exc_type, exc_value, traceback):
        """Stop acting like a context manager."""
        self.restore_flag()

    def decorate(self, func):
        """Decorates a function to enable the waffle flag."""
        @wraps(func)
        def _give_me_waffles(*args, **kwargs):
            self.make_flag()
            try:
                func(*args, **kwargs)
            finally:
                self.restore_flag()
        return _give_me_waffles

    def make_flag(self):
        """Ensure that the flag is created and has the correct values."""
        Flag.objects.update_or_create(name=self.flagname, defaults=self.kwargs)

    def restore_flag(self):
        """Ensure that the flag is reset back to its original value."""
        Flag.objects.filter(name=self.flagname).delete()
        if self.origflag is not None:
            self.origflag.id = self.origid
            self.origflag.save()
