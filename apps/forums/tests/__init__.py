from datetime import datetime
import random
from string import letters

from django.template.defaultfilters import slugify

from forums.models import Forum, Thread, Post
from users.tests import user
from sumo.tests import LocalizingClient, TestCase, with_save


class ForumTestCase(TestCase):
    client_class = LocalizingClient


class OldForumTestCase(TestCase):
    fixtures = ['users.json', 'posts.json', 'forums_permissions.json']
    client_class = LocalizingClient


@with_save
def forum(**kwargs):
    if 'name' not in kwargs:
        kwargs['name'] = ''.join(random.choice(letters)
                                 for x in xrange(15))
    if 'slug' not in kwargs:
        kwargs['slug'] = slugify(kwargs['name'])
    return Forum(**kwargs)


@with_save
def thread(**kwargs):
    defaults = dict(
        created=datetime.now(),
        title=''.join(random.choice(letters) for x in xrange(15)))
    defaults.update(kwargs)
    if 'creator' not in kwargs and 'creator_id' not in kwargs:
        defaults['creator'] = user(save=True)
    if 'forum' not in kwargs and 'forum_id' not in kwargs:
        defaults['forum'] = forum(save=True)
    return Thread(**defaults)


@with_save
def post(**kwargs):
    defaults = dict()
    defaults.update(kwargs)
    if 'author' not in kwargs and 'author_id' not in kwargs:
        defaults['author'] = user(save=True)
    if 'thread' not in kwargs and 'thread_id' not in kwargs:
        defaults['thread'] = thread(save=True)
    return Post(**defaults)
