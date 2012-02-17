from customercare.models import Tweet, Reply
from sumo.tests import with_save


next_tweet_id = 1


@with_save
def tweet(**kwargs):
    """Return a Tweet with valid default values or the ones passed in.

    Args:
        save: whether to save the Tweet before returning it
        text: the `text` attribute of the Tweet's raw_json
    """
    global next_tweet_id
    defaults = {'locale': 'en', 'raw_json':
        '{"iso_language_code": "en", "text": "%s", '
        '"created_at": "Thu, 23 Sep 2010 13:58:06 +0000", '
        '"profile_image_url": '
        '"http://a1.twimg.com/profile_images/1117809237/cool_cat_normal.jpg", '
        '"source": "&lt;a href=&quot;http://www.tweetdeck.com&quot; '
            'rel=&quot;nofollow&quot;&gt;TweetDeck&lt;/a&gt;", '
            '"from_user": "__jimcasey__", "from_user_id": 142651388, '
            '"to_user_id": null, "geo": null, "id": 25309168521, '
            '"metadata": {"result_type": "recent"}}' %
            kwargs.pop('text', 'Hey #Firefox')}  # TODO: Escape quotes and such
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
        'raw_json':
        '{"iso_language_code": "en", "text": "%s", '
        '"created_at": "Thu, 23 Sep 2010 13:58:06 +0000", '
        '"profile_image_url": '
        '"http://a1.twimg.com/profile_images/1117809237/cool_cat_normal.jpg", '
        '"source": "&lt;a href=&quot;http://www.tweetdeck.com&quot; '
            'rel=&quot;nofollow&quot;&gt;TweetDeck&lt;/a&gt;", '
            '"from_user": "__jimcasey__", "from_user_id": 142651388, '
            '"to_user_id": null, "geo": null, "id": 25309168521, '
            '"metadata": {"result_type": "recent"}}' %
            kwargs.pop('text', 'Hey #Firefox')}  # TODO: Escape quotes and such
    defaults.update(kwargs)
    return Reply(**defaults)
