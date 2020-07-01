import factory
from django.test.client import RequestFactory
from django.test.utils import override_settings

from kitsune.search.models import Synonym
from kitsune.sumo.tests import TestCase


# Dummy request for passing to question_searcher() and brethren.
dummy_request = RequestFactory().get('/')


@override_settings(ES_LIVE_INDEXING=True)
class ElasticTestCase(TestCase):
    """Base class for Elastic Search tests, providing some conveniences"""
    search_tests = True


class SynonymFactory(factory.DjangoModelFactory):
    class Meta:
        model = Synonym

    from_words = "foo, bar"
    to_words = "baz"
