from datetime import timedelta

from kitsune.dashboards.readouts import CONTRIBUTOR_READOUTS
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.models import Document, HelpfulVote
from kitsune.wiki.tests import ApprovedRevisionFactory


class LocalizationDashTests(TestCase):
    def test_redirect_to_contributor_dash(self):
        """Should redirect to Contributor Dash if the locale is the default"""
        response = self.client.get(reverse("dashboards.localization", locale="en-US"), follow=True)
        self.assertRedirects(response, reverse("dashboards.contributors", locale="en-US"))


class ContributorDashTests(TestCase):
    def test_main_view(self):
        """Assert the top page of the contributor dash resolves, renders."""
        response = self.client.get(reverse("dashboards.contributors", locale="en-US"))
        self.assertEqual(200, response.status_code)

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
        self.assertEqual(200, response.status_code)

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
        self.assertEqual(200, response.status_code)
        assert change_comment in response.content


def _add_vote_in_past(rev, vote, days_back):
    v = HelpfulVote(revision=rev, helpful=vote)
    v.created = v.created - timedelta(days=days_back)
    v.save()
