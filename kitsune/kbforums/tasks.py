from celery import shared_task

from kitsune.kbforums import events
from kitsune.kbforums.models import Post
from kitsune.tidings.utils import get_users


@shared_task
def fire(event_cls_name, post_id, exclude_user_ids=None):
    post = Post.objects.get(id=post_id)
    event_cls = getattr(events, event_cls_name)
    event_cls(post).fire(exclude=get_users(exclude_user_ids))
