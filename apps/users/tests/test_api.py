import json

from nose import SkipTest
from nose.tools import eq_

from sumo.helpers import urlparams
from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class UsernamesTests(TestCase):
    """Test the usernames API method."""
    fixtures = ['users.json']
    url = reverse('users.api.usernames', locale='en-US')

    def setUp(self):
        self.client.login(username='jsocol', password='testpass')

    def tearDown(self):
        self.client.logout()

    def test_no_query(self):
        res = self.client.get(self.url)
        eq_(200, res.status_code)
        eq_('[]', res.content)

    def test_query(self):
        res = self.client.get(urlparams(self.url, u='a'))
        eq_(200, res.status_code)
        data = json.loads(res.content)
        eq_(2, len(data))

    def test_post(self):
        res = self.client.post(self.url)
        eq_(405, res.status_code)

    def test_logged_out(self):
        self.client.logout()
        res = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(403, res.status_code)
