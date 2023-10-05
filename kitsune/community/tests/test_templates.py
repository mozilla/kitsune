from pyquery import PyQuery as pq

from kitsune.forums.tests import ThreadFactory
from kitsune.questions.tests import AnswerFactory
from kitsune.search.tests import Elastic7TestCase
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import ContributorFactory, UserFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory, RevisionFactory


class UserSearchTests(Elastic7TestCase):
    """Tests for the Community Hub user search page."""

    search_tests = True

    def test_no_results(self):
        UserFactory(username="foo", profile__name="Foo Bar")
        response = self.client.get(urlparams(reverse("community.search"), q="baz"))
        self.assertEqual(response.status_code, 200)
        assert b"No users were found" in response.content

    def test_results(self):
        UserFactory(username="foo", profile__name="Foo Bar")
        UserFactory(username="bam", profile__name="Bar Bam")

        # Searching for "bam" should return 1 user.
        response = self.client.get(urlparams(reverse("community.search"), q="bam"))

        self.assertEqual(response.status_code, 200)
        doc = pq(response.content)
        self.assertEqual(len(doc(".results-user")), 1)

        # Searching for "bar" should return both users.
        response = self.client.get(urlparams(reverse("community.search"), q="bar"))

        self.assertEqual(response.status_code, 200)
        doc = pq(response.content)
        self.assertEqual(len(doc(".results-user")), 2)


class LandingTests(Elastic7TestCase):
    """Tests for the Community Hub landing page."""

    search_tests = True

    def test_top_contributors(self):
        """Verify the top contributors appear."""
        # FIXME: Change this to batch creation
        RevisionFactory(document__locale="en-US")
        d = DocumentFactory(locale="es")
        RevisionFactory(document=d)
        RevisionFactory(document=d)
        AnswerFactory(creator=ContributorFactory())
        AnswerFactory(creator=ContributorFactory())
        AnswerFactory(creator=ContributorFactory())

        response = self.client.get(urlparams(reverse("community.home")))
        self.assertEqual(response.status_code, 200)
        doc = pq(response.content)
        self.assertEqual(1, len(doc("ul.kb > li")))
        self.assertEqual(2, len(doc("ul.l10n > li")))
        self.assertEqual(3, len(doc("ul.questions > li")))

    def test_wiki_section(self):
        """Verify the wiki doc appears on the landing page."""
        # If "Mozilla News" article doesn't exist, home page
        # should still work and omit the section.
        response = self.client.get(urlparams(reverse("community.home")))
        self.assertEqual(response.status_code, 200)
        doc = pq(response.content)
        self.assertEqual(len(doc("#doc-content")), 0)

        # Create the "Mozilla News" article and verify it on home page.
        d = DocumentFactory(title="Community Hub News", slug="community-hub-news")
        rev = ApprovedRevisionFactory(document=d, content="splendid")
        d.current_revision = rev
        d.save()
        response = self.client.get(urlparams(reverse("community.home")))
        self.assertEqual(response.status_code, 200)
        doc = pq(response.content)
        community_news = doc("#doc-content")
        self.assertEqual(len(community_news), 1)
        assert "splendid" in community_news.text()

    def test_recent_threads(self):
        """Verify the Community Discussions section."""
        ThreadFactory(forum__slug="contributors", title="we are SUMO!!!!!!")

        response = self.client.get(urlparams(reverse("community.home")))
        self.assertEqual(response.status_code, 200)
        doc = pq(response.content)
        self.assertEqual(1, len(doc("#recent-threads")))
        assert "we are SUMO!" in doc("#recent-threads ul").html()


class TopContributorsTests(Elastic7TestCase):
    """Tests for the Community Hub top contributors page."""

    search_tests = True

    def test_invalid_area(self):
        response = self.client.get(
            urlparams(reverse("community.top_contributors", args=["foobar"]))
        )
        self.assertEqual(404, response.status_code)

    def test_top_questions(self):
        a1 = AnswerFactory(creator=ContributorFactory())
        a2 = AnswerFactory(creator=ContributorFactory())

        response = self.client.get(
            urlparams(reverse("community.top_contributors", args=["questions"]))
        )
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        self.assertEqual(2, len(doc(".results-user")))
        assert a1.creator.username in str(response.content)
        assert a2.creator.username in str(response.content)

    def test_top_kb(self):
        d = DocumentFactory(locale="en-US")
        r1 = RevisionFactory(document=d)
        r2 = RevisionFactory(document=d)

        response = self.client.get(urlparams(reverse("community.top_contributors", args=["kb"])))
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        self.assertEqual(2, len(doc(".results-user")))
        assert r1.creator.username in str(response.content)
        assert r2.creator.username in str(response.content)

    def test_top_l10n(self):
        d = DocumentFactory(locale="es")
        r1 = RevisionFactory(document=d)
        r2 = RevisionFactory(document=d)

        response = self.client.get(urlparams(reverse("community.top_contributors", args=["l10n"])))
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        self.assertEqual(2, len(doc(".results-user")))
        assert r1.creator.username in str(response.content)
        assert r2.creator.username in str(response.content)
