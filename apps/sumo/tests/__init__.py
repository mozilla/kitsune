from functools import wraps
from os import listdir
from os.path import join, dirname
import re
from smtplib import SMTPRecipientsRefused

from django.conf import settings
from django.test.client import Client
from django.test.utils import override_settings

from nose.tools import eq_
from test_utils import TestCase as OriginalTestCase

from sumo.urlresolvers import reverse, split_path
import sumo


get = lambda c, v, **kw: c.get(reverse(v, **kw), follow=True)
post = lambda c, v, data={}, **kw: c.post(reverse(v, **kw), data, follow=True)


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


def send_mail_raise_smtp(subject, content, from_emal, recipients):
    """Patch mail.send_mail with this in your tests to check what happens when
    an email fails to send."""
    raise SMTPRecipientsRefused(recipients=recipients)


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
            assert engines >= creates, ("There weren't as many "
                'occurrences of "ENGINE=InnoDB" as of "CREATE TABLE" in '
                'migration %s.' % filename)
            assert encodings >= creates, ("There weren't as many "
                'UTF-8 declarations as "CREATE TABLE" occurrences in '
                'migration %s.' % filename)


class MobileTestCase(TestCase):
    def setUp(self):
        super(MobileTestCase, self).setUp()
        self.client.cookies[settings.MOBILE_COOKIE] = 'on'


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
