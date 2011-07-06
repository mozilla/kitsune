from nose.tools import eq_

from dashboards.readouts import CONTRIBUTOR_READOUTS
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from users.tests import user, group


class LocalizationDashTests(TestCase):
    def test_redirect_to_contributor_dash(self):
        """Should redirect to Contributor Dash if the locale is the default"""
        response = self.client.get(reverse('dashboards.localization',
                                           locale='en-US'),
                                   follow=True)
        self.assertRedirects(response, reverse('dashboards.contributors',
                                               locale='en-US'))


class ContributorDashTests(TestCase):
    def test_main_view(self):
        """Assert the top page of the contributor dash resolves, renders."""
        response = self.client.get(reverse('dashboards.contributors',
                                           locale='en-US'))
        eq_(200, response.status_code)

    def test_detail_view(self):
        """Assert the detail page of the contributor dash resolves, renders."""
        response = self.client.get(reverse('dashboards.contributors_detail',
            args=[CONTRIBUTOR_READOUTS[CONTRIBUTOR_READOUTS.keys()[0]].slug],
            locale='en-US'))
        eq_(200, response.status_code)


class DefaultDashboardRedirect(TestCase):
    def setUp(self):
        super(DefaultDashboardRedirect, self).setUp()
        self.user = user(save=True)
        self.client.login(username=self.user.username, password='testpass')
        self.group = group(name='Contributors', save=True)

    def test_redirect_non_contributor(self):
        """Test redirect from /dashboard to dashboard/wecome."""
        r = self.client.get(reverse('dashboards.default', locale='en-US'),
                            follow=False)
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/dashboard/welcome', r['location'])

    def test_redirect_contributor(self):
        """Test redirect from /dashboard to dashboard/forums."""
        self.user.groups.add(self.group)
        r = self.client.get(reverse('dashboards.default', locale='en-US'),
                            follow=False)
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/dashboard/forums', r['location'])
