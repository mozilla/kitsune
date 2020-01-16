from nose.tools import eq_

from kitsune.kbadge.tests import AwardFactory, BadgeFactory
from kitsune.sumo.tests import LocalizingClient, TestCase
from kitsune.sumo.urlresolvers import reverse


class AwardsListTests(TestCase):
    client = LocalizingClient()

    def test_list_empty(self):
        resp = self.client.get(reverse('kbadge.awards_list'), follow=True)
        eq_(200, resp.status_code)

    def test_list_with_awards(self):
        b = BadgeFactory()
        a1 = AwardFactory(description='A1 AWARD', badge=b)
        a2 = AwardFactory(description='A2 AWARD', badge=b)
        a3 = AwardFactory(description='A3 AWARD', badge=b)

        resp = self.client.get(reverse('kbadge.awards_list'), follow=True)
        eq_(200, resp.status_code)
        self.assertContains(resp, a1.user.username)
        self.assertContains(resp, a1.get_absolute_url())
        self.assertContains(resp, a2.user.username)
        self.assertContains(resp, a2.get_absolute_url())
        self.assertContains(resp, a3.user.username)
        self.assertContains(resp, a3.get_absolute_url())


class AwardDetailsTests(TestCase):
    def test_details_page(self):
        # This is a just basic test to make sure the template loads.
        a1 = AwardFactory(description='A1 AWARD')

        resp = self.client.get(a1.get_absolute_url(), follow=True)
        eq_(200, resp.status_code)
