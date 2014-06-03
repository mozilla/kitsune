from nose.tools import eq_

from pyquery import PyQuery as pq

from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.helpers import urlparams
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import user, profile


class UserSearchTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_no_results(self):
        profile(name='Foo Bar', user=user(username='foo', save=True))

        self.refresh()

        response = self.client.get(
            urlparams(reverse('community.search'), q='baz'))

        eq_(response.status_code, 200)
        assert 'No users were found' in response.content

    def test_results(self):
        profile(name='Foo Bar', user=user(username='foo', save=True))
        profile(name='Bar Bam', user=user(username='bam', save=True))

        self.refresh()

        # Searching for "bam" should return 1 user.
        response = self.client.get(
            urlparams(reverse('community.search'), q='bam'))

        eq_(response.status_code, 200)
        doc = pq(response.content)
        eq_(len(doc('.results-user')), 1)

        # Searching for "bar" should return both users.
        response = self.client.get(
            urlparams(reverse('community.search'), q='bar'))

        eq_(response.status_code, 200)
        doc = pq(response.content)
        eq_(len(doc('.results-user')), 2)
