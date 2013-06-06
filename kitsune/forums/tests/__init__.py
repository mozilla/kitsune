from datetime import datetime
import uuid

from django.template.defaultfilters import slugify

from kitsune.forums.models import Forum, Thread, Post
from kitsune.users.tests import user
from kitsune.sumo.tests import LocalizingClient, TestCase, with_save


class ForumTestCase(TestCase):
    client_class = LocalizingClient


@with_save
def forum(**kwargs):
    if 'name' not in kwargs:
        kwargs['name'] = str(uuid.uuid4())
    if 'slug' not in kwargs:
        kwargs['slug'] = slugify(kwargs['name'])
    return Forum(**kwargs)


@with_save
def thread(**kwargs):
    defaults = dict(
        created=datetime.now(),
        title=str(uuid.uuid4()))
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
        # The thread creator should match the post author if the
        # thread doesn't exist yet.
        kw = {}
        if 'author' in defaults:
            kw['creator'] = defaults['author']
        else:
            kw['creator_id'] = defaults['author_id']
        defaults['thread'] = thread(save=True, **kw)
    return Post(**defaults)
