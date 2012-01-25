import json

from django.conf import settings
from django.core.cache import cache

from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse
from sumo.tests import TestCase


class CannedResponsesTestCase(TestCase):
    """Canned responses tests."""

    def test_list_canned_responses(self):
        """Listing canned responses works as expected."""

        r = self.client.get(reverse('customercare.landing'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        responses_plain = doc('#accordion').text()

        # Listing all categories
        assert "Welcome and Thanks" in responses_plain
        assert "Using Firefox" in responses_plain
        assert "Support" in responses_plain
        assert "Get Involved" in responses_plain

        # Listing all responses
        eq_(22, len(doc('#accordion a.reply-topic')))

    def test_list_canned_responses_nondefault_locale(self):
        """Listing canned responses gives all snippets regardless of locale."""

        r = self.client.get(reverse('customercare.landing', locale='es'),
                            follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)

        # Listing all responses, l10n-agnostic (English if not in Verbatim).
        eq_(22, len(doc('#accordion a.reply-topic')))


class TweetListTestCase(TestCase):
    """Tests for the list of tweets."""

    def test_fallback_message(self):
        """Fallback message when there are no tweets."""
        r = self.client.get(reverse('customercare.landing'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        assert doc('#tweets-wrap .warning-box'), (
               'Fallback message is not showing up.')


class StatsTests(TestCase):
    """Tests for the activity and contributors stats."""

    def setUp(self):
        super(StatsTests, self).setUp()
        with open('apps/customercare/tests/stats.json') as f:
            self.json_data = json.load(f)

    def tearDown(self):
        cache.delete(settings.CC_TWEET_ACTIVITY_CACHE_KEY)
        cache.delete(settings.CC_TOP_CONTRIB_CACHE_KEY)
        super(StatsTests, self).tearDown()

    def test_activity_contributors(self):
        """Activity and contributors stats are both set."""
        cache.set(settings.CC_TWEET_ACTIVITY_CACHE_KEY,
                  self.json_data['activity'],
                  settings.CC_STATS_CACHE_TIMEOUT)
        cache.set(settings.CC_TOP_CONTRIB_CACHE_KEY,
                  self.json_data['contributors'],
                  settings.CC_STATS_CACHE_TIMEOUT)
        r = self.client.get(reverse('customercare.landing'), follow=True)
        eq_(200, r.status_code)

    def test_activity_only(self):
        """Only activity stats are set."""
        cache.set(settings.CC_TWEET_ACTIVITY_CACHE_KEY,
                  self.json_data['activity'],
                  settings.CC_STATS_CACHE_TIMEOUT)
        r = self.client.get(reverse('customercare.landing'), follow=True)
        eq_(200, r.status_code)

    def test_contributors_only(self):
        """Only contributors stats are set."""
        cache.set(settings.CC_TOP_CONTRIB_CACHE_KEY,
                  self.json_data['contributors'],
                  settings.CC_STATS_CACHE_TIMEOUT)
        r = self.client.get(reverse('customercare.landing'), follow=True)
        eq_(200, r.status_code)
