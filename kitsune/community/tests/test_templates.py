from nose.tools import eq_

from pyquery import PyQuery as pq

from kitsune.customercare.tests import ReplyFactory
from kitsune.forums.tests import ThreadFactory
from kitsune.questions.tests import AnswerFactory
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import DocumentFactory, RevisionFactory, ApprovedRevisionFactory


class UserSearchTests(ElasticTestCase):
    """Tests for the Community Hub user search page."""
    client_class = LocalizingClient

    def test_no_results(self):
        UserFactory(username='foo', profile__name='Foo Bar')
        self.refresh()
        response = self.client.get(urlparams(reverse('community.search'), q='baz'))
        eq_(response.status_code, 200)
        assert 'No users were found' in response.content

    def test_results(self):
        UserFactory(username='foo', profile__name='Foo Bar')
        UserFactory(username='bam', profile__name='Bar Bam')

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


class LandingTests(ElasticTestCase):
    """Tests for the Community Hub landing page."""
    client_class = LocalizingClient

    def test_top_contributors(self):
        """Verify the top contributors appear."""
        # FIXME: Change this to batch creation
        RevisionFactory(document__locale='en-US')
        d = DocumentFactory(locale='es')
        RevisionFactory(document=d)
        RevisionFactory(document=d)
        AnswerFactory()
        AnswerFactory()
        AnswerFactory()
        ReplyFactory()
        ReplyFactory()
        ReplyFactory()
        ReplyFactory()

        self.refresh()

        response = self.client.get(urlparams(reverse('community.home')))
        eq_(response.status_code, 200)
        doc = pq(response.content)
        eq_(1, len(doc('ul.kb > li')))
        eq_(2, len(doc('ul.l10n > li')))
        eq_(3, len(doc('ul.questions > li')))
        eq_(4, len(doc('ul.army-of-awesome > li')))

    def test_wiki_section(self):
        """Verify the wiki doc appears on the landing page."""
        # If "Mozilla News" article doesn't exist, home page
        # should still work and omit the section.
        response = self.client.get(urlparams(reverse('community.home')))
        eq_(response.status_code, 200)
        doc = pq(response.content)
        eq_(len(doc('#doc-content')), 0)

        # Create the "Mozilla News" article and verify it on home page.
        d = DocumentFactory(title='Community Hub News', slug='community-hub-news')
        rev = ApprovedRevisionFactory(document=d, content='splendid')
        d.current_revision = rev
        d.save()
        response = self.client.get(urlparams(reverse('community.home')))
        eq_(response.status_code, 200)
        doc = pq(response.content)
        community_news = doc('#doc-content')
        eq_(len(community_news), 1)
        assert 'splendid' in community_news.text()

    def test_recent_threads(self):
        """Verify the Community Discussions section."""
        ThreadFactory(forum__slug='contributors', title='we are SUMO!!!!!!')

        self.refresh()

        response = self.client.get(urlparams(reverse('community.home')))
        eq_(response.status_code, 200)
        doc = pq(response.content)
        eq_(1, len(doc('#recent-threads')))
        assert 'we are SUMO!' in doc('#recent-threads li').html()


class TopContributorsTests(ElasticTestCase):
    """Tests for the Community Hub top contributors page."""
    client_class = LocalizingClient

    def test_invalid_area(self):
        response = self.client.get(urlparams(
            reverse('community.top_contributors', args=['foobar'])))
        eq_(404, response.status_code)

    def test_top_army_of_awesome(self):
        r1 = ReplyFactory()
        r2 = ReplyFactory()

        self.refresh()

        response = self.client.get(urlparams(
            reverse('community.top_contributors', args=['army-of-awesome'])))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(2, len(doc('li.results-user')))
        assert str(r1.user.username) in response.content
        assert str(r2.user.username) in response.content

    def test_top_questions(self):
        a1 = AnswerFactory()
        a2 = AnswerFactory()

        self.refresh()

        response = self.client.get(urlparams(
            reverse('community.top_contributors', args=['questions'])))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(2, len(doc('li.results-user')))
        assert str(a1.creator.username) in response.content
        assert str(a2.creator.username) in response.content

    def test_top_kb(self):
        d = DocumentFactory(locale='en-US')
        r1 = RevisionFactory(document=d)
        r2 = RevisionFactory(document=d)

        self.refresh()

        response = self.client.get(urlparams(reverse('community.top_contributors', args=['kb'])))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(2, len(doc('li.results-user')))
        assert str(r1.creator.username) in response.content
        assert str(r2.creator.username) in response.content

    def test_top_l10n(self):
        d = DocumentFactory(locale='es')
        r1 = RevisionFactory(document=d)
        r2 = RevisionFactory(document=d)

        self.refresh()

        response = self.client.get(urlparams(
            reverse('community.top_contributors', args=['l10n'])))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(2, len(doc('li.results-user')))
        assert str(r1.creator.username) in response.content
        assert str(r2.creator.username) in response.content
