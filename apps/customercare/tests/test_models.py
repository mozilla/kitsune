from nose.tools import eq_, raises

from customercare.models import Tweet
from customercare.tests import tweet
from sumo.tests import TestCase


class TweetTests(TestCase):
    """Tests for the Tweet model"""

    def test_latest(self):
        """Test the latest() class method when there is a latest tweet."""
        NUM = 2
        for x in range(NUM):
            last = tweet(save=True)
        eq_(last.tweet_id, Tweet.latest().tweet_id)

    @raises(Tweet.DoesNotExist)
    def test_latest_does_not_exist(self):
        """latest() should throw DoesNotExist when there are no tweets."""
        Tweet.latest()
