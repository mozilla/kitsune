# -*- coding: utf-8 -*-
import copy
import json
from datetime import datetime, timedelta

from django.conf import settings
from django.test.utils import override_settings

from mock import patch
from nose import SkipTest
from nose.tools import eq_

from customercare.tests import tweet, reply
from customercare.cron import (_filter_tweet, _get_oldest_tweet, purge_tweets,
                               get_customercare_stats)
from customercare.models import Tweet, Reply
from sumo.tests import TestCase
from sumo.redis_utils import redis_client, RedisError


class TwitterCronTestCase(TestCase):
    tweet_template = {
        "profile_image_url": (
            "http://a3.twimg.com/profile_images/688562959/"
            "jspeis_gmail.com_852af0c8__1__normal.jpg"),
        "created_at": "Mon, 25 Oct 2010 18:12:20 +0000",
        "from_user": "jspeis",
        "metadata": {
            "result_type": "recent",
        },
        "to_user_id": None,
        "text": "giving the Firefox 4 beta a whirl",
        "id": 28713868836,
        "from_user_id": 2385258,
        "geo": None,
        "iso_language_code": "en",
        "source": "&lt;a href=&quot;http://twitter.com/&quot;&gt;web&lt;/a&gt;"
    }

    def setUp(self):
        self.tweet = copy.deepcopy(self.tweet_template)

    def test_unfiltered(self):
        """Do not filter tweets without a reason."""
        eq_(self.tweet, _filter_tweet(self.tweet))

    def test_mentions(self):
        """Filter out mentions."""
        self.tweet['text'] = 'Hey @someone!'
        assert _filter_tweet(self.tweet) is None

    def test_firefox_mention(self):
        """Don't filter out @firefox mentions."""
        self.tweet['text'] = 'Hey @firefox!'
        eq_(self.tweet, _filter_tweet(self.tweet))

    def test_firefoxbrasil_mention(self):
        """Don't filter out @FirefoxBrasil mentions."""
        self.tweet['text'] = 'Olá @FirefoxBrasil!'
        eq_(self.tweet, _filter_tweet(self.tweet))

    def test_replies(self):
        """Filter out replies."""
        self.tweet['to_user_id'] = 12345
        self.tweet['text'] = '@someone Hello!'
        assert _filter_tweet(self.tweet) is None

    def test_firefox_replies(self):
        """Don't filter out @firefox replies."""
        self.tweet['to_user_id'] = 2142731
        self.tweet['text'] = '@firefox Hello!'
        eq_(self.tweet, _filter_tweet(self.tweet))

    def test_firefoxbrasil_replies(self):
        """Don't filter out @FirefoxBrasil replies."""
        self.tweet['to_user_id'] = 150793437
        self.tweet['text'] = '@FirefoxBrasil Olá!'
        eq_(self.tweet, _filter_tweet(self.tweet))

    def test_retweets(self):
        """No retweets or 'via'"""
        self.tweet['text'] = 'RT @someone: Firefox is awesome'
        assert _filter_tweet(self.tweet) is None

        self.tweet['text'] = 'Firefox is awesome (via @someone)'
        assert _filter_tweet(self.tweet) is None

    def test_links(self):
        """Filter out tweets with links."""
        self.tweet['text'] = 'Just watching: http://youtube.com/12345 Fun!'
        assert _filter_tweet(self.tweet) is None

    def test_fx4status(self):
        """Ensure fx4status tweets are filtered out."""
        self.tweet['from_user'] = 'fx4status'
        assert _filter_tweet(self.tweet) is None

    def test_username_and_tweet_contain_firefox(self):
        self.tweet['from_user'] = 'ilovefirefox4ever'
        self.tweet['text'] = 'My Firefox crashes :-( Any advice?'
        assert _filter_tweet(self.tweet) is not None


class GetOldestTweetTestCase(TestCase):

    def setUp(self):
        tweet(
            tweet_id=1,
            locale='en',
            created='2010-09-23 13:50:00',
            save=True
        )
        tweet(
            tweet_id=2,
            locale='en',
            created='2010-09-23 13:53:00',
            save=True
        )
        tweet(
            tweet_id=3,
            created='2010-09-23 13:57:00',
            locale='en',
            save=True
        )

    def test_get_oldest_tweet_exists(self):
        eq_(1, _get_oldest_tweet('en', 2).pk)
        eq_(2, _get_oldest_tweet('en', 1).pk)
        eq_(3, _get_oldest_tweet('en', 0).pk)

    def test_get_oldest_tweet_offset_too_big(self):
        eq_(None, _get_oldest_tweet('en', 100))

    def test_get_oldest_tweet_none_exist(self):
        eq_(None, _get_oldest_tweet('fr', 0))
        eq_(None, _get_oldest_tweet('fr', 1))
        eq_(None, _get_oldest_tweet('fr', 20))


class PurgeTweetsTestCase(TestCase):
    """Tweets are deleted for each locale."""

    def setUp(self):
        # 4 'en' and 2 'r'
        for i in range(0, 6):
            if i >= 4:
                locale = 'ro'
            else:
                locale = 'en'

            tweet(
                locale=locale,
                created=datetime.now() - timedelta(hours=i),
                save=True
            )

    @patch.object(settings._wrapped, 'CC_MAX_TWEETS', 1)
    def test_purge_tweets_two_locales(self):
        purge_tweets()
        eq_(1, Tweet.objects.filter(locale='en').count())
        eq_(1, Tweet.objects.filter(locale='ro').count())

    @patch.object(settings._wrapped, 'CC_MAX_TWEETS', 3)
    def test_purge_tweets_one_locale(self):
        purge_tweets()
        eq_(3, Tweet.objects.filter(locale='en').count())
        # Does not touch Romanian tweets.
        eq_(2, Tweet.objects.filter(locale='ro').count())

    @patch.object(settings._wrapped, 'CC_MAX_TWEETS', 0)
    def test_purge_all_tweets(self):
        purge_tweets()
        eq_(0, Tweet.objects.count())


@override_settings(CC_TOP_CONTRIB_LIMIT=2)
class TopContributors(TestCase):

    def setUp(self):
        now = datetime.now()
        two_days_ago = now - timedelta(days=2)
        two_weeks_ago = now - timedelta(days=14)
        two_months_ago = now - timedelta(days=60)

        # Moe has the most in the last day, curly has the most in the last
        # week, larry has the most in the last month, and moe has the most
        # overall.
        data = {
            'moe': [(now, 3), (two_days_ago, 2), (two_months_ago, 20)],
            'curly': [(two_days_ago, 6), (two_weeks_ago, 2)],
            'larry': [(two_weeks_ago, 10), (two_months_ago, 4)]
        }
        for who, what in data.items():
            for when, how_many in what:
                for _ in range(how_many):
                    reply(created=when, twitter_username=who, save=True)

    def test_setUp(self):
        """Since the setup above is non-trivial, test it."""
        five_days_ago = datetime.now() - timedelta(days=5)
        eq_(Reply.objects.count(), 47)
        eq_(Reply.objects.filter(twitter_username='moe').count(), 25)
        eq_(Reply.objects.filter(twitter_username='curly').count(), 8)
        eq_(Reply.objects.filter(twitter_username='larry').count(), 14)
        eq_(Reply.objects.filter(created__lt=five_days_ago).count(), 36)

    @override_settings(CC_TOP_CONTRIB_SORT='all')
    def test_all_range(self):
        """Test that data looks about right for the 'all' date range."""
        stats = get_customercare_stats()
        # Limited to two results from @override_settings on this class.
        eq_(len(stats), 2)
        eq_(stats[0]['twitter_username'], 'moe')
        eq_(stats[1]['twitter_username'], 'larry')

        eq_(stats[0]['all'], 25)
        eq_(stats[0]['1m'], 5)
        eq_(stats[0]['1w'], 5)
        eq_(stats[0]['1d'], 3)

    @override_settings(CC_TOP_CONTRIB_SORT='1w')
    def test_week_range(self):
        """Data looks about right for the 'one week' date range.

        Test two date ranges to ensure that the code is paying attention to
        settings.py.
        """
        stats = get_customercare_stats()
        # Limited to two results from @override_settings on this class.
        eq_(len(stats), 2)
        eq_(stats[0]['twitter_username'], 'curly')
        eq_(stats[1]['twitter_username'], 'moe')

        eq_(stats[0]['all'], 8)
        eq_(stats[0]['1m'], 8)
        eq_(stats[0]['1w'], 6)
        eq_(stats[0]['1d'], 0)

    def test_stored_in_redis(self):
        key = settings.CC_TOP_CONTRIB_CACHE_KEY
        try:
            redis = redis_client(name='default')
            # Other tests are lame and don't clean up after themselves.
            # This also verifies that Redis is alive and well.
            redis.delete(key)
        except RedisError:
            raise SkipTest

        get_customercare_stats()

        blob = redis.get(key)
        stats = json.loads(blob)
        eq_(len(stats), 2)
