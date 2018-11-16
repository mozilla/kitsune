import re
from django.test.client import RequestFactory
from django.test.utils import override_settings

import factory
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import IndexTemplate
from elasticsearch_dsl.connections import get_connection
from elasticsearch_dsl.query import MatchAll

from kitsune.search.models import Synonym
from kitsune.sumo.tests import TestCase
from django.core.management import call_command

# Dummy request for passing to question_searcher() and brethren.
dummy_request = RequestFactory().get('/')


@override_settings(ES_LIVE_INDEXING=True)
class ElasticTestCase(TestCase):
    """Base class for Elastic Search tests, providing some conveniences"""
    search_tests = True


class ElasticDSLTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super(ElasticDSLTestCase, cls).setUpClass()
        call_command('esindex')

    def delete_all_documents(self):
        # Use low level Elasticsearch API to delete all the documents
        query = {
            "query": {
                "match_all": {}
            }
        }
        connection = get_connection()
        connection.delete_by_query(index='_all', body=query, conflicts='proceed')
        connection.indices.clear_cache()

    def setUp(self):
        self.delete_all_documents()

        super(ElasticDSLTestCase, self).setUp()

    def tearDown(self):
        self.delete_all_documents()

        super(ElasticDSLTestCase, self).tearDown()


class SynonymFactory(factory.DjangoModelFactory):
    class Meta:
        model = Synonym

    from_words = "foo, bar"
    to_words = "baz"
