from django.conf import settings
from django.test.client import RequestFactory
from django.test.utils import override_settings

from elasticutils.contrib.django import get_es
from nose import SkipTest
from test_utils import TestCase

from search import es_utils
from search.models import generate_tasks


# Dummy request for passing to question_searcher() and brethren.
# There's no reason to use test_utils' RequestFactory.
dummy_request = RequestFactory().get('/')


@override_settings(ES_LIVE_INDEXING=True)
class ElasticTestCase(TestCase):
    """Base class for Elastic Search tests, providing some conveniences"""
    skipme = False

    @classmethod
    def setUpClass(cls):
        super(ElasticTestCase, cls).setUpClass()

        if not getattr(settings, 'ES_URLS'):
            cls.skipme = True
            return

        # try to connect to ES and if it fails, skip ElasticTestCases.
        try:
            get_es().health()
        except es_utils.ES_EXCEPTIONS:
            cls.skipme = True
            return

        # Swap out for better versions that use ES_INDEX_PREFIX.
        cls._old_read_index = es_utils.READ_INDEX
        cls._old_write_index = es_utils.WRITE_INDEX
        es_utils.READ_INDEX = settings.ES_INDEX_PREFIX + u'sumo_testindex'
        es_utils.WRITE_INDEX = settings.ES_INDEX_PREFIX + u'sumo_testindex'

    @classmethod
    def tearDownClass(cls):
        super(ElasticTestCase, cls).tearDownClass()
        if not cls.skipme:
            # Restore old settings.
            es_utils.READ_INDEX = cls._old_read_index
            es_utils.WRITE_INDEX = cls._old_write_index

    def setUp(self):
        if self.skipme:
            raise SkipTest

        super(ElasticTestCase, self).setUp()
        self.setup_indexes()

    def tearDown(self):
        super(ElasticTestCase, self).tearDown()
        self.teardown_indexes()

    def refresh(self, run_tasks=True):
        index = es_utils.WRITE_INDEX

        if run_tasks:
            # Any time we're doing a refresh, we're making sure that
            # the index is ready to be queried. Given that, it's
            # almost always the case that we want to run all the
            # generated tasks, then refresh.
            generate_tasks()

        get_es().refresh(index)
        get_es().health(wait_for_status='yellow')

    def reindex_and_refresh(self):
        """Reindexes anything in the db"""
        from search.es_utils import es_reindex_cmd
        es_reindex_cmd()
        self.refresh(run_tasks=False)

    def setup_indexes(self, empty=False, wait=True):
        """(Re-)create WRITE_INDEX"""
        from search.es_utils import recreate_index
        recreate_index()
        get_es().health(wait_for_status='yellow')

    def teardown_indexes(self):
        """Tear down WRITE_INDEX"""
        es_utils.delete_index(es_utils.WRITE_INDEX)
