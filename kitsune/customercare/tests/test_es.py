from nose.tools import eq_

from kitsune.customercare.models import ReplyMetricsMappingType
from kitsune.customercare.tests import reply
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.users.tests import user


class AnswerMetricsTests(ElasticTestCase):
    def test_add_and_delete(self):
        """Adding a reply should add it to the index.

        Deleting should delete it.
        """
        r = reply(save=True)
        self.refresh()
        eq_(ReplyMetricsMappingType.search().count(), 1)

        r.delete()
        self.refresh()
        eq_(ReplyMetricsMappingType.search().count(), 0)

    def test_data_in_index(self):
        """Verify the data we are indexing."""
        u = user(save=True)
        r = reply(user=u, locale='de', save=True)
        self.refresh()

        eq_(ReplyMetricsMappingType.search().count(), 1)
        results = ReplyMetricsMappingType.search().values_dict('locale', 'creator_id')
        results = ReplyMetricsMappingType.reshape(results)
        data = results[0]

        eq_(data['locale'], r.locale)
        eq_(data['creator_id'], r.user_id)
