from nose.tools import eq_

from flagit.tests import TestCaseBase
from sumo.urlresolvers import reverse
from users.tests import user


class FlagitTestPermissions(TestCaseBase):
    """Test our new permission required decorator."""
    def setUp(self):
        super(FlagitTestPermissions, self).setUp()
        self.user = user(save=True)

    def test_permission_required(self):
        url = reverse('flagit.queue', force_locale=True)
        resp = self.client.get(url)
        eq_(302, resp.status_code)

        self.client.login(username=self.user.username, password='testpass')
        resp = self.client.get(url)
        eq_(403, resp.status_code)

        self.client.login(username='admin', password='testpass')
        resp = self.client.get(url)
        eq_(200, resp.status_code)
