import json
from datetime import datetime

import factory

from kitsune.customercare.models import Tweet, TwitterAccount, Reply
from kitsune.sumo.tests import FuzzyUnicode
from kitsune.users.tests import UserFactory


class RawJsonFactory(factory.Factory):
    class Meta:
        @staticmethod
        def model(**kwargs):
            # Unpack keys like foo__bar=1 into {'foo': {'bar': 1}}
            data = {}
            for key_path, val in list(kwargs.items()):
                keys = key_path.split('__')
                cursor = data
                for key in keys[:-1]:
                    cursor = cursor.setdefault(key, {})
                cursor[keys[-1]] = val
            return json.dumps(data)

    created_at = factory.LazyAttribute(lambda r: datetime.now())
    geo = None
    id = factory.fuzzy.FuzzyInteger(10000000)
    iso_language_code = 'en'
    metadata__result_type = 'recent'
    source = (
        '&lt;a href=&quot;http://www.tweetdeck.com&quot; '
        'rel=&quot;nofollow&quot;&gt;TweetDeck&lt;/a&gt;')
    text = 'Hey #Firefox'
    to_user_id = None
    user__screen_name = FuzzyUnicode()
    user__profile_image_url = 'http://example.com/profile_image.jpg'
    user__profile_image_url_https = 'https://example.com/profile_image.jpg'

    @factory.lazy_attribute
    def created_at(data, **kwargs):
        created_at = datetime.now()
        return created_at.strftime('%a, %d %b %Y %H:%M:%S +0000')


class TweetFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tweet

    locale = 'en'
    raw_json = factory.SubFactory(RawJsonFactory)
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
    raw_json = factory.SubFactory(RawJsonFactory)
    reply_to_tweet_id = factory.fuzzy.FuzzyInteger(1000000)
    tweet_id = factory.fuzzy.FuzzyInteger(1000000)
    twitter_username = factory.fuzzy.FuzzyText()
    user = factory.SubFactory(UserFactory)
