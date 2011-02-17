from django.conf import settings

from mock import patch_object
from nose.tools import eq_

from customercare.models import Tweet
from customercare.views import _get_tweets
from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class TweetListTestCase(TestCase):
    """Tests for the customer care tweet list."""

    fixtures = ['tweets.json']

    def test_limit(self):
        """Do not return more than LIMIT tweets."""
        tweets = _get_tweets(limit=2)
        eq_(len(tweets), 2)

    def test_max_id(self):
        """Ensure max_id offset works."""
        tweets_1 = _get_tweets()
        assert tweets_1

        # Select max_id from the first list
        max_id = tweets_1[3]['id']
        tweets_2 = _get_tweets(max_id=max_id)
        assert tweets_2

        # Make sure this id is not in the result, and all tweets are older than
        # max_id.
        for tweet in tweets_2:
            assert tweet['id'] < max_id

    def test_hide_tweets(self):
        """Try hiding tweets."""
        hide_tweet = lambda id: self.client.post(
            reverse('customercare.hide_tweet', locale='en-US'),
            {'id': id})

        tw = Tweet.objects.no_cache().filter(reply_to=None, hidden=False)[0]
        r = hide_tweet(tw.tweet_id)
        eq_(r.status_code, 200)

        # Re-fetch from database. Should be hidden.
        tw = Tweet.objects.no_cache().get(tweet_id=tw.tweet_id)
        eq_(tw.hidden, True)

        # Hiding it again should work.
        r = hide_tweet(tw.tweet_id)
        eq_(r.status_code, 200)

    def test_hide_tweets_with_replies(self):
        """Hiding tweets with replies is not allowed."""
        tw = Tweet.objects.filter(reply_to=None)[0]
        tw.reply_to = 123
        tw.save()

        r = self.client.post(
            reverse('customercare.hide_tweet', locale='en-US'),
            {'id': tw.tweet_id})
        eq_(r.status_code, 400)

    def test_hide_tweets_invalid_id(self):
        """Invalid tweet IDs shouldn't break anything."""
        hide_tweet = lambda id: self.client.post(
            reverse('customercare.hide_tweet', locale='en-US'),
            {'id': id})

        r = hide_tweet(123)
        eq_(r.status_code, 404)

        r = hide_tweet('cheesecake')
        eq_(r.status_code, 400)

    @patch_object(settings._wrapped, 'CC_ALLOW_REMOVE', False)
    def test_hide_tweets_disabled(self):
        """Do not allow hiding tweets if feature is disabled."""
        tw = Tweet.objects.filter(reply_to=None)[0]
        r = self.client.post(
            reverse('customercare.hide_tweet', locale='en-US'),
            {'id': tw.tweet_id})
        eq_(r.status_code, 418)  # Don't tell a teapot to brew coffee.
