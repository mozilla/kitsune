from datetime import timedelta
import json

from django.conf import settings

from nose import SkipTest
from nose.tools import eq_

from dashboards.cron import cache_most_unhelpful_kb_articles
from dashboards.readouts import CONTRIBUTOR_READOUTS
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from sumo.utils import redis_client
from users.tests import user, group
from wiki.models import HelpfulVote
from wiki.tests import revision


class LocalizationDashTests(TestCase):
    def setUp(self):
        super(LocalizationDashTests, self).setUp()
        try:
            self.redis = redis_client('helpfulvotes')
            self.redis.flushdb()
        except (KeyError, AttributeError):
            pass

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


def _add_vote_in_past(rev, vote, days_back):
    v = HelpfulVote(revision=rev, helpful=vote)
    v.created = v.created - timedelta(days=days_back)
    v.save()


class HelpfulVotesGraphTests(TestCase):
    def setUp(self):
        super(HelpfulVotesGraphTests, self).setUp()
        self.user = user(save=True)
        self.client.login(username=self.user.username, password='testpass')
        self.group = group(name='Contributors', save=True)
        # Without this, there were unrelated failures with l10n dashboard
        try:
            self.redis = redis_client('helpfulvotes')
            self.redis.flushdb()
            self.REDIS_KEY = settings.HELPFULVOTES_UNHELPFUL_KEY
        except (KeyError, AttributeError):
            raise SkipTest

    def tearDown(self):
        try:
            self.redis.flushdb()
        except (KeyError, AttributeError):
            raise SkipTest
        super(HelpfulVotesGraphTests, self).tearDown()

    def test_no_data(self):
        response = self.client.get(
                                  reverse('dashboards.get_helpful_graph_async',
                                  locale='en-US'))
        eq_(200, response.status_code)
        result = json.loads(response.content)
        eq_(0, len(result['data'][0]['data']))

    def test_response_data(self):
        r = revision(save=True)
        r.created = r.created - timedelta(days=90)
        r.save()

        for x in range(0, 4):
            _add_vote_in_past(r, 0, 15)

        cache_most_unhelpful_kb_articles()

        response = self.client.get(
                                  reverse('dashboards.get_helpful_graph_async',
                                  locale='en-US'))
        eq_(200, response.status_code)
        result = json.loads(response.content)

        eq_(1, len(result['data'][0]['data']))
        eq_(r.document.title, result['data'][0]['data'][0]['title'])
        eq_(0.0, result['data'][0]['data'][0]['colorsize'])
        eq_('0.00', result['data'][0]['data'][0]['currperc'])


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
