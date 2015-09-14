from nose.tools import eq_

from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


class TestCoolSearch(TestCase):
    def test_search(self):
        response = self.client.get(
            reverse('coolsearch.search', locale='en-US'),
        )
        eq_(response.status_code, 200)
