from datetime import timedelta, datetime

from nose.tools import eq_

from kitsune.announcements.tests import AnnouncementFactory
from kitsune.dashboards.readouts import CONTRIBUTOR_READOUTS
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory
from kitsune.wiki.models import HelpfulVote, Document
from kitsune.wiki.tests import LocaleFactory, ApprovedRevisionFactory


class LocalizationDashTests(TestCase):
    def test_redirect_to_contributor_dash(self):
        """Should redirect to Contributor Dash if the locale is the default"""
        response = self.client.get(reverse("dashboards.localization", locale="en-US"), follow=True)
        self.assertRedirects(response, reverse("dashboards.contributors", locale="en-US"))


def LocalizationDashAnnouncementsTests(TestCase):
    def setUp(self):
        self.locale1 = LocaleFactory(locale="es")

        self.u1 = UserFactory()
        self.u2 = UserFactory()
        self.u3 = UserFactory()

        self.u1.is_superuser = 1
        self.u1.save()

        self.locale1.leaders.add(self.u2)
        self.locale1.save()

        self.announcement = AnnouncementFactory(
            creator=self.u2,
            locale=self.locale1,
            content="Look at me!",
            show_after=datetime(2012, 1, 1, 0, 0, 0),
        )

    def test_show_create(self):
        self.client.login(username=self.u1.username, password="testpass")
        resp = self.client.get(reverse("dashboards.localization"))
        self.assertContains(resp, 'id="create-announcement"')

    def test_show_for_authed(self):
        self.client.login(username=self.u2.username, password="testpass")
        resp = self.client.get(reverse("dashboards.localization"))
        self.assertContains(resp, 'id="create-announcement"')

    def test_hide_for_not_authed(self):
        self.client.login(username=self.u3.username, password="testpass")
        resp = self.client.get(reverse("dashboards.localization"))
        self.assertNotContains(resp, 'id="create-announcement"')

    def test_hide_for_anon(self):
        resp = self.client.get(reverse("dashboards.localization"))
        self.assertNotContains(resp, 'id="create-announcement"')


class ContributorDashTests(TestCase):
    def test_main_view(self):
        """Assert the top page of the contributor dash resolves, renders."""
        response = self.client.get(reverse("dashboards.contributors", locale="en-US"))
        eq_(200, response.status_code)

    def test_detail_view(self):
        """Assert the detail page of the contributor dash resolves, renders."""
        readoutKey = list(CONTRIBUTOR_READOUTS.keys())[0]
        response = self.client.get(
            reverse(
                "dashboards.contributors_detail",
                args=[CONTRIBUTOR_READOUTS[readoutKey].slug],
                locale="en-US",
            )
        )
        eq_(200, response.status_code)

    def test_needs_change_comment_is_shown(self):
        # If there are already 10 documents, this is probably going to
        # fail anyways, so be quick and obvious about it.
        assert Document.objects.count() < 10

        change_comment = b"lorem OMG FIX ipsum dolor"
        ApprovedRevisionFactory(
            document__needs_change=True,
            document__needs_change_comment=change_comment,
        )

        response = self.client.get(reverse("dashboards.contributors", locale="en-US"))
        eq_(200, response.status_code)
        assert change_comment in response.content


def _add_vote_in_past(rev, vote, days_back):
    v = HelpfulVote(revision=rev, helpful=vote)
    v.created = v.created - timedelta(days=days_back)
    v.save()
