import json
from datetime import datetime

from kitsune.customercare.models import Tweet, Reply
from kitsune.sumo.tests import with_save


next_tweet_id = 1
tweet_created = datetime.now().strftime('%a, %d %b %Y %H:%M:%S')


@with_save
def tweet(**kwargs):
    """Return a Tweet with valid default values or the ones passed in.

    :arg save: whether to save the Tweet before returning it
    :arg text: the `text` attribute of the Tweet's raw_json
    """
    global next_tweet_id
    # TODO: Escape quotes and such
    defaults = {
        'locale': 'en',
        'raw_json': json.dumps({
            'iso_language_code': 'en',
            'text': kwargs.pop('text', 'Hey #Firefox'),
            'created_at': tweet_created,
            'source': '&lt;a href=&quot;http://www.tweetdeck.com&quot; '
                      'rel=&quot;nofollow&quot;&gt;TweetDeck&lt;/a&gt;',
            'user': {
                'screen_name': '__jimcasey__',
                'profile_image_url': 'http://a1.twimg.com/profile_images/'
                                     '1117809237/cool_cat_normal.jpg',
                'profile_image_url_https': 'http://si0.twimg.com/'
                                           'profile_images/1117809237/'
                                           'cool_cat_normal.jpg',
            },
            'to_user_id': None,
            'geo': None,
            'id': 25309168521,
            'metadata': {
                'results_type': 'recent',
            }
        })
    }

    defaults.update(kwargs)
    if 'tweet_id' not in kwargs:
        defaults['tweet_id'] = next_tweet_id
        next_tweet_id += 1

    return Tweet(**defaults)


@with_save
def reply(**kwargs):
    """Return a Reply with valid default values or the ones passed in.

    :arg save: whether to save the Tweet before returning it
    :arg text: the `text` attribute of the Tweet's raw_json
    """
    defaults = {
        'locale': 'en',
        'twitter_username': 'r1cky',
        'tweet_id': 12345,
        'reply_to_tweet_id': 123456,
        'raw_json': json.dumps({
            'iso_language_code': 'en',
            'text': kwargs.pop('text', 'Hey #Firefox'),
            'created_at': 'Thu, 23 Sep 2010 13:58:06 +0000',
            'source': '&lt;a href=&quot;http://www.tweetdeck.com&quot; '
                'rel=&quot;nofollow&quot;&gt;TweetDeck&lt;/a&gt;',
            'user': {
                'screen_name': '__jimcasey__',
                'profile_image_url': 'http://a1.twimg.com/profile_images/'
                                     '1117809237/cool_cat_normal.jpg',
                'profile_image_url_https': 'http://si0.twimg.com/'
                                           'profile_images/1117809237/'
                                           'cool_cat_normal.jpg',
            },
            'to_user_id': None,
            'geo': None,
            'id': 25309168521,
            'metadata': {'result_type': 'recent'}
        })
    }
    defaults.update(kwargs)
    return Reply(**defaults)
