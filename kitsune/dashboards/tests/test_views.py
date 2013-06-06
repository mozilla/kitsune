from datetime import timedelta, datetime

from nose.tools import eq_

from kitsune.announcements.tests import announcement
from kitsune.dashboards.readouts import CONTRIBUTOR_READOUTS
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import user
from kitsune.wiki.models import HelpfulVote
from kitsune.wiki.tests import locale


class LocalizationDashTests(TestCase):
    def test_redirect_to_contributor_dash(self):
        """Should redirect to Contributor Dash if the locale is the default
        """
        response = self.client.get(reverse('dashboards.localization',
                                           locale='en-US'),
                                   follow=True)
        self.assertRedirects(response, reverse('dashboards.contributors',
                                               locale='en-US'))


def LocalizationDashAnnouncementsTests(TestCase):
    def setUp(self):
        self.locale1 = locale(save=True, locale='es')

        self.u1 = user(save=True)
        self.u2 = user(save=True)
        self.u3 = user(save=True)

        self.u1.is_superuser = 1
        self.u1.save()

        self.locale1.leaders.add(self.u2)
        self.locale1.save()

        self.announcement = announcement(save=True, creator=self.u2,
            locale=self.locale1, content="Look at me!",
            show_after=datetime(2012, 01, 01, 0, 0, 0))

    def test_show_create(self):
        self.client.login(username=self.u1.username, password='testpass')
        resp = self.client.get(reverse('dashboards.localization'))
        self.assertContains(resp, 'id="create-announcement"')

    def test_show_for_authed(self):
        self.client.login(username=self.u2.username, password='testpass')
        resp = self.client.get(reverse('dashboards.localization'))
        self.assertContains(resp, 'id="create-announcement"')

    def test_hide_for_not_authed(self):
        self.client.login(username=self.u3.username, password='testpass')
        resp = self.client.get(reverse('dashboards.localization'))
        self.assertNotContains(resp, 'id="create-announcement"')

    def test_hide_for_anon(self):
        resp = self.client.get(reverse('dashboards.localization'))
        self.assertNotContains(resp, 'id="create-announcement"')


class ContributorDashTests(TestCase):
    def test_main_view(self):
        """Assert the top page of the contributor dash resolves, renders."""
        response = self.client.get(reverse('dashboards.contributors',
                                           locale='en-US'))
        eq_(200, response.status_code)

    def test_detail_view(self):
        """Assert the detail page of the contributor dash resolves, renders.
        """
        response = self.client.get(reverse('dashboards.contributors_detail',
            args=[CONTRIBUTOR_READOUTS[CONTRIBUTOR_READOUTS.keys()[0]].slug],
            locale='en-US'))
        eq_(200, response.status_code)


def _add_vote_in_past(rev, vote, days_back):
    v = HelpfulVote(revision=rev, helpful=vote)
    v.created = v.created - timedelta(days=days_back)
    v.save()
