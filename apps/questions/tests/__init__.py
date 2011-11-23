from datetime import datetime

from django.conf import settings
from django.template.defaultfilters import slugify

from elasticutils import get_es

from nose.tools import eq_
from nose import SkipTest

from questions.models import Question
from sumo.tests import LocalizingClient, TestCase


class TestCaseBase(TestCase):
    """Base TestCase for the Questions app test cases."""

    fixtures = ['users.json', 'questions.json']
    client_class = LocalizingClient

    def setUp(self):
        q = Question.objects.get(pk=1)
        q.last_answer_id = 1
        q.save()

        # create a new cache key for top contributors to avoid conflict
        # TODO: May be able to go away once we flush memcache between tests.
        self.orig_tc_cache_key = settings.TOP_CONTRIBUTORS_CACHE_KEY
        settings.TOP_CONTRIBUTORS_CACHE_KEY += slugify(datetime.now())

    def tearDown(self):
        settings.TOP_CONTRIBUTORS_CACHE_KEY = self.orig_tc_cache_key


class TaggingTestCaseBase(TestCaseBase):
    """Base testcase with additional setup for testing tagging"""

    fixtures = TestCaseBase.fixtures + ['taggit.json']


def tags_eq(tagged_object, tag_names):
    """Assert that the names of the tags on tagged_object are tag_names."""
    eq_(sorted([t.name for t in tagged_object.tags.all()]),
        sorted(tag_names))


# TODO: Have to define this here, since I need the data that TestCaseBase
# generates.  Should we turn ESTestCase into a mixin?
class ESTestCase(TestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(ESTestCase, cls).setUpClass()
        if getattr(settings, 'ES_HOSTS', None) is None:
            raise SkipTest

        # Delete test indexes if they exist.
        cls.es = get_es()
        for index in settings.ES_INDEXES.values():
            cls.es.delete_index_if_exists(index)

        from search.utils import es_reindex

        es_reindex()

    @classmethod
    def tearDownClass(cls):
        for index in settings.ES_INDEXES.values():
            cls.es.delete_index_if_exists(index)
        super(ESTestCase, cls).tearDownClass()
