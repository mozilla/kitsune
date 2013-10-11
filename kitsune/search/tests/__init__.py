from django.conf import settings
from django.test.client import RequestFactory
from django.test.utils import override_settings

from elasticutils.contrib.django import get_es
from nose import SkipTest
from test_utils import TestCase

from kitsune.search import es_utils
from kitsune.search.models import generate_tasks


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

    def setUp(self):
        if self.skipme:
            raise SkipTest

        super(ElasticTestCase, self).setUp()
        self.setup_indexes()

    def tearDown(self):
        super(ElasticTestCase, self).tearDown()
        self.teardown_indexes()

    def refresh(self, run_tasks=True):
        es = get_es()

        if run_tasks:
            # Any time we're doing a refresh, we're making sure that
            # the index is ready to be queried. Given that, it's
            # almost always the case that we want to run all the
            # generated tasks, then refresh.
            generate_tasks()

        for index in es_utils.all_write_indexes():
            es.refresh(index)

        es.health(wait_for_status='yellow')

    def reindex_and_refresh(self):
        """Reindexes anything in the db"""
        from kitsune.search.es_utils import es_reindex_cmd
        es_reindex_cmd()
        self.refresh(run_tasks=False)

    def setup_indexes(self, empty=False, wait=True):
        """(Re-)create write index"""
        from kitsune.search.es_utils import recreate_indexes
        recreate_indexes()
        get_es().health(wait_for_status='yellow')

    def teardown_indexes(self):
        """Tear down write index"""
        for index in es_utils.all_write_indexes():
            es_utils.delete_index(index)
