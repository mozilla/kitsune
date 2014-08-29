from nose.tools import eq_

from django.contrib.auth.models import User

from pyquery import PyQuery as pq

from kitsune.customercare.tests import reply
from kitsune.forums.tests import thread, forum
from kitsune.questions.tests import answer
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.helpers import urlparams
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import user, profile
from kitsune.wiki.tests import document, revision


class UserSearchTests(ElasticTestCase):
    """Tests for the Community Hub user search page."""
    client_class = LocalizingClient

    def test_no_results(self):
        profile(name='Foo Bar', user=user(username='foo', save=True))

        self.refresh()

        response = self.client.get(
            urlparams(reverse('community.search'), q='baz'))

        eq_(response.status_code, 200)
        assert 'No users were found' in response.content

    def test_results(self):
        profile(name='Foo Bar', user=user(username='foo', save=True))
        profile(name='Bar Bam', user=user(username='bam', save=True))

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
        d = document(locale='en-US', save=True)
        revision(document=d, save=True)
        d = document(locale='es', save=True)
        revision(document=d, save=True)
        revision(document=d, save=True)
        answer(save=True)
        answer(save=True)
        answer(save=True)
        reply(user=user(save=True), save=True)
        reply(user=user(save=True), save=True)
        reply(user=user(save=True), save=True)
        reply(user=user(save=True), save=True)

        for u in User.objects.all():
            profile(user=u)

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
        d = document(
            title='Community Hub News', slug='community-hub-news', save=True)
        rev = revision(
            document=d, content='splendid', is_approved=True, save=True)
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
        f = forum(slug='contributors', save=True)
        t = thread(forum=f, title='we are SUMO!!!!!!', save=True)

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
        r1 = reply(user=user(save=True), save=True)
        r2 = reply(user=user(save=True), save=True)
        profile(user=r1.user)
        profile(user=r2.user)

        self.refresh()

        response = self.client.get(urlparams(
            reverse('community.top_contributors', args=['army-of-awesome'])))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(2, len(doc('li.results-user')))
        assert r1.user.username in response.content
        assert r2.user.username in response.content

    def test_top_questions(self):
        a1 = answer(save=True)
        a2 = answer(save=True)
        profile(user=a1.creator)
        profile(user=a2.creator)

        self.refresh()

        response = self.client.get(urlparams(
            reverse('community.top_contributors', args=['questions'])))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(2, len(doc('li.results-user')))
        assert a1.creator.username in response.content
        assert a2.creator.username in response.content

    def test_top_kb(self):
        d = document(locale='en-US', save=True)
        r1 = revision(document=d, save=True)
        r2 = revision(document=d, save=True)
        profile(user=r1.creator)
        profile(user=r2.creator)

        self.refresh()

        response = self.client.get(urlparams(
            reverse('community.top_contributors', args=['kb'])))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(2, len(doc('li.results-user')))
        assert r1.creator.username in response.content
        assert r2.creator.username in response.content

    def test_top_l10n(self):
        d = document(locale='es', save=True)
        r1 = revision(document=d, save=True)
        r2 = revision(document=d, save=True)
        profile(user=r1.creator)
        profile(user=r2.creator)

        self.refresh()

        response = self.client.get(urlparams(
            reverse('community.top_contributors', args=['l10n'])))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(2, len(doc('li.results-user')))
        assert r1.creator.username in response.content
        assert r2.creator.username in response.content
