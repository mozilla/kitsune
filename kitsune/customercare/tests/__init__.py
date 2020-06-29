import json
from datetime import datetime

import factory
from faker import Faker

from kitsune.customercare.models import Tweet, TwitterAccount, Reply
from kitsune.users.tests import UserFactory


def raw_json():
    created_at = datetime.now()
    fake = Faker()
    return json.dumps({
        "created_at": created_at.strftime('%a, %d %b %Y %H:%M:%S +0000'),
        "geo": None,
        "id": fake.pyint(),
        "iso_language_code": 'en',
        "metadata": {
            "result_type": 'recent'
        },
        "source": (
            '&lt;a href=&quot;http://www.tweetdeck.com&quot; '
            'rel=&quot;nofollow&quot;&gt;TweetDeck&lt;/a&gt;'),
        "text": 'Hey #Firefox',
        "to_user_id": None,
        "user": {
            "screen_name": fake.pystr(),
            "profile_image_url": 'http://example.com/profile_image.jpg',
            "profile_image_url_https": 'https://example.com/profile_image.jpg'
        }
    })


class TweetFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tweet

    locale = 'en'
    raw_json = factory.LazyFunction(raw_json)
    tweet_id = factory.Sequence(lambda n: n)


class TwitterAccountFactory(factory.DjangoModelFactory):
    class Meta:
        model = TwitterAccount

    username = factory.fuzzy.FuzzyText()
    banned = factory.fuzzy.FuzzyChoice([True, False])
    ignored = factory.fuzzy.FuzzyChoice([True, False])


class ReplyFactory(factory.DjangoModelFactory):
    class Meta:
        model = Reply

    locale = 'en'
    raw_json = factory.LazyFunction(raw_json)
    reply_to_tweet_id = factory.fuzzy.FuzzyInteger(1000000)
    tweet_id = factory.fuzzy.FuzzyInteger(1000000)
    twitter_username = factory.fuzzy.FuzzyText()
    user = factory.SubFactory(UserFactory)
