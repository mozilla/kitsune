from datetime import datetime
import random

from django.conf import settings

from customercare.models import (Tweet, CategoryMembership, CannedCategory,
                                 CannedResponse)
from sumo.tests import with_save


def cc_category(save=False, **kwargs):
    """Return a canned category.

    Save it if save=True or if a `responses` kwarg is nonempty.

    """
    responses = kwargs.pop('responses', [])
    save = save or responses  # Adding responses forces save.
    defaults = {'title': str(datetime.now()),
                'weight': random.choice(range(50)),
                'locale': settings.LANGUAGE_CODE}
    defaults.update(kwargs)

    category = CannedCategory(**defaults)
    if save or responses:
        category.save()
    # Add responses to this category.
    for response, weight in responses:
        CategoryMembership.objects.create(
            category=category, response=response, weight=weight)

    return category


def cc_response(save=False, **kwargs):
    """Return a canned response.

    Save it if save=True or if a `categories` kwarg is nonempty.

    """
    categories = kwargs.pop('categories', [])
    save = save or categories  # Adding categories forces save.

    defaults = {'title': str(datetime.now()),
                'response': 'Test response (%s).' % random.choice(range(50)),
                'locale': settings.LANGUAGE_CODE}
    defaults.update(kwargs)

    response = CannedResponse(**defaults)
    if save or categories:
        response.save()
    # Add categories to this response.
    for category, weight in categories:
        weight = random.choice(range(50))
        CategoryMembership.objects.create(
            category=category, response=response, weight=weight)

    return response


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
