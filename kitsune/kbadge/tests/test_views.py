from nose.tools import eq_

from kitsune.kbadge.tests import award, badge
from kitsune.sumo.tests import LocalizingClient, TestCase
from kitsune.sumo.urlresolvers import reverse


class AwardsListTests(TestCase):
    client = LocalizingClient()

    def test_list_empty(self):
        resp = self.client.get(reverse('badger.awards_list'), follow=True)
        eq_(200, resp.status_code)

    def test_list_with_awards(self):
        b = badge(save=True)
        a1 = award(description=u'A1 AWARD', badge=b, save=True)
        a2 = award(description=u'A2 AWARD', badge=b, save=True)
        a3 = award(description=u'A3 AWARD', badge=b, save=True)

        resp = self.client.get(reverse('badger.awards_list'), follow=True)
        eq_(200, resp.status_code)
        self.assertContains(resp, a1.description)
        self.assertContains(resp, a1.get_absolute_url())
        self.assertContains(resp, a2.description)
        self.assertContains(resp, a2.get_absolute_url())
        self.assertContains(resp, a3.description)
        self.assertContains(resp, a3.get_absolute_url())


class AwardDetailsTests(TestCase):
    def test_details_page(self):
        # This is a just basic test to make sure the template loads.
        b = badge(save=True)
        a1 = award(description=u'A1 AWARD', badge=b, save=True)

        resp = self.client.get(a1.get_absolute_url(), follow=True)
        eq_(200, resp.status_code)
