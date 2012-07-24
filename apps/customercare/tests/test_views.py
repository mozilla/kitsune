from datetime import datetime, timedelta
import json

from django.conf import settings

from mock import patch, Mock
from nose.tools import eq_
from test_utils import RequestFactory

from customercare.tests import tweet, reply
from customercare.models import Tweet, Reply
from customercare.views import _get_tweets, _count_tweets
from customercare.views import twitter_post
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse


class TweetListTests(TestCase):
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
        tw.reply_to_id = 25309168529
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

    @patch.object(settings._wrapped, 'CC_ALLOW_REMOVE', False)
    def test_hide_tweets_disabled(self):
        """Do not allow hiding tweets if feature is disabled."""
        tw = Tweet.objects.filter(reply_to=None)[0]
        r = self.client.post(
            reverse('customercare.hide_tweet', locale='en-US'),
            {'id': tw.tweet_id})
        eq_(r.status_code, 418)  # Don't tell a teapot to brew coffee.


class CountTests(TestCase):
    def test_count_tweets(self):
        """Test filtering when counting tweets"""

        tweet(created=datetime.now() - timedelta(days=3), save=True)
        tweet(created=datetime.now(), save=True)
        tw = Tweet.latest()

        # create a reply
        tweet(reply_to=tw, hidden=True, save=True)

        count_answered = _count_tweets(locale=tw.locale, filter='answered')
        eq_(count_answered, 1)

        count_unanswered = _count_tweets(locale=tw.locale, filter='unanswered')
        eq_(count_unanswered, 1)

        yesterday = datetime.now() - timedelta(days=1)
        count_recent_unanswered = _count_tweets(locale=tw.locale,
                                                filter='unanswered',
                                                since=yesterday)
        eq_(count_recent_unanswered, 0)


class FilterTestCase(TestCase):
    client_class = LocalizingClient

    def _tweet_list(self, filter):
        """Return the content of async-fetched tweet list.

        Also, assert the request returns a 200.

        """
        response = self.client.get(
            reverse('customercare.more_tweets'),
            {'filter': filter})
        eq_(response.status_code, 200)
        return response.content


class FilterTests(FilterTestCase):
    """Test tweet filtering"""

    def setUp(self):
        """Make a tweet, an answer to it, an unanswered tweet, and a hidden
        one."""
        super(FilterTests, self).setUp()

        tweet(text='YO_UNANSWERED').save()
        cry_for_help = tweet(text='YO_HELP_ME', save=True)
        tweet(text='YO_REPLY', reply_to=cry_for_help).save()
        tweet(text='YO_HIDDEN', hidden=True).save()

    def _test_a_filter(self, filter, should_show_unanswered,
                       should_show_answered, should_show_reply,
                       should_show_hidden):
        """Ensure the given filter shows the tweets specified."""
        content = self._tweet_list(filter)
        assert ('YO_UNANSWERED' in content) == should_show_unanswered
        assert ('YO_HELP_ME' in content) == should_show_answered
        assert ('YO_REPLY' in content) == should_show_reply
        assert ('YO_HIDDEN' in content) == should_show_hidden

    def test_unanswered(self):
        self._test_a_filter('unanswered', True, False, False, False)

    def test_answered(self):
        self._test_a_filter('answered', False, True, True, False)

    def test_all(self):
        self._test_a_filter('all', True, True, True, True)

    def test_recent(self):
        self._test_a_filter('recent', True, True, True, False)

    def test_bogus(self):
        """Test a bogus filter, which should fall back to Recent."""
        self._test_a_filter('bogus', True, True, True, False)


class FilterCachingTests(FilterTestCase):
    """Test interaction of caching with filters"""

    def test_caching(self):
        """Ensure refiltering the list after replying shows the replied-to
        tweet as such."""
        # We need at least one existing answer to get the list of answered
        # tweets to cache:
        question = tweet(save=True)
        tweet(reply_to=question).save()

        # Make a sad, sad, unanswered tweet:
        cry_for_help = tweet(text='YO_UNANSWERED', save=True)

        # Cache the list of answered tweets:
        self._tweet_list('answered')

        # Reply to the lonely tweet:
        tweet(text='YO_REPLY', reply_to=cry_for_help).save()

        # And make sure we can immediately see that we replied:
        assert 'YO_UNANSWERED' in self._tweet_list('answered')


class TweetReplyTests(TestCase):
    """Test for the twitter_post view."""
    client_class = LocalizingClient

    def test_post_reply(self):
        # Create a Tweet to reply to.
        Tweet.objects.create(
            pk=1,
            raw_json='{}',
            locale='en',
            created=datetime.now())

        # Create a request and mock all the required properties and methods.
        request = RequestFactory().post(
            reverse('customercare.twitter_post'),
            {'reply_to': 1,
             'content': '@foobar try Aurora! #fxhelp'})
        request.session = {}
        request.twitter = Mock()
        request.twitter.authed = True
        request.twitter.api = Mock()
        return_value = Mock()
        return_value.__dict__ = {
            'id': 123456790,
            'text': '@foobar try Aurora! #fxhelp',
            'created_at': datetime.now(), }
        return_value.author = Mock()
        return_value.author.__dict__ = {
            'lang': 'en',
            'id': 42,
            'screen_name': 'r1cky',
            'profile_image_url': 'http://example.com/profile.jpg',
            'profile_image_url_https': 'https://example.com/profile.jpg', }
        request.twitter.api.update_status.return_value = return_value

        # Pass the request to the view and verify response.
        response = twitter_post(request)
        eq_(200, response.status_code)

        # Verify the reply was inserted with the right data.
        reply = Reply.objects.all()[0]
        eq_('r1cky', reply.twitter_username)
        eq_(1, reply.reply_to_tweet_id)
        eq_('@foobar try Aurora! #fxhelp', json.loads(reply.raw_json)['text'])
