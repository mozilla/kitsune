from nose.tools import eq_, raises

from kitsune.customercare.models import Tweet
from kitsune.customercare.tests import TweetFactory
from kitsune.sumo.tests import TestCase


class TweetTests(TestCase):
    """Tests for the Tweet model"""

    def test_latest(self):
        """Test the latest() class method when there is a latest tweet."""
        TweetFactory()
        last = TweetFactory()
        eq_(last.tweet_id, Tweet.latest().tweet_id)

    @raises(Tweet.DoesNotExist)
    def test_latest_does_not_exist(self):
        """latest() should throw DoesNotExist when there are no tweets."""
        Tweet.latest()
