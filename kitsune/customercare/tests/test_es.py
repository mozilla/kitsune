from nose.tools import eq_

from kitsune.customercare.models import ReplyMetricsMappingType
from kitsune.customercare.tests import ReplyFactory
from kitsune.search.tests.test_es import ElasticTestCase


class AnswerMetricsTests(ElasticTestCase):
    def test_add_and_delete(self):
        """Adding a reply should add it to the index.

        Deleting should delete it.
        """
        r = ReplyFactory()
        self.refresh()
        eq_(ReplyMetricsMappingType.search().count(), 1)

        r.delete()
        self.refresh()
        eq_(ReplyMetricsMappingType.search().count(), 0)

    def test_data_in_index(self):
        """Verify the data we are indexing."""
        r = ReplyFactory(locale='de')
        self.refresh()

        eq_(ReplyMetricsMappingType.search().count(), 1)
        data = ReplyMetricsMappingType.search()[0]

        eq_(data['locale'], r.locale)
        eq_(data['creator_id'], r.user_id)
