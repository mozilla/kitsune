from functools import wraps
from os import listdir
from os.path import join, dirname
import re
from smtplib import SMTPRecipientsRefused

from django.conf import settings
from django.test.client import Client

from nose.tools import eq_
from nose import SkipTest
from test_utils import TestCase  # just for others to import
from waffle.models import Flag

import sumo
from sumo.urlresolvers import reverse, split_path

from elasticutils import get_es


get = lambda c, v, **kw: c.get(reverse(v, **kw), follow=True)
post = lambda c, v, data={}, **kw: c.post(reverse(v, **kw), data, follow=True)


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


class ElasticTestCase(TestCase):
    """Base class for Elastic Search tests, providing some conveniences"""
    def setUp(self):
        super(ElasticTestCase, self).setUp()
        self.setup_indexes()
        Flag.objects.create(name='elasticsearch', everyone=True)

    def tearDown(self):
        self.teardown_indexes()
        super(ElasticTestCase, self).tearDown()

    def refresh(self, index='default'):
        # Any time we're doing a refresh, we're making sure that the
        # index is ready to be queried.  Given that, it's almost
        # always the case that we want to run all the generated tasks,
        # then refresh.
        from search.models import generate_tasks
        generate_tasks()

        es = get_es()
        es.refresh(settings.ES_INDEXES[index], timesleep=0)

    def setup_indexes(self):
        """(Re-)create ES indexes."""
        from search.es_utils import es_reindex

        if getattr(settings, 'ES_HOSTS', None) is None:
            raise SkipTest

        # TODO: Don't bother scanning through model objects and indexing any
        # that exist. None of our ES tests use any fixtures, so incremental
        # indexing will suffice for them.
        es_reindex()

        # TODO: This is kind of bad.  If setup_indexes gets called in
        # a setUp and that setUp at some point throws an exception, we
        # could end up in a situation where setUp throws an exception,
        # so tearDown doesn't get called and we never set
        # ES_LIVE_INDEXING to False and thus ES_LIVE_INDEXING is True
        # for a bunch of tests it shouldn't be true for.
        #
        # For settings like this, it's better to mock it in the class
        # because the mock will set it back regardless of whether the
        # test fails.
        settings.ES_LIVE_INDEXING = True

    def teardown_indexes(self):
        es = get_es()
        for index in settings.ES_INDEXES.values():
            es.delete_index_if_exists(index)

        settings.ES_LIVE_INDEXING = False


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
