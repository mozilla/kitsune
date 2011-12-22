import logging

from django.db import transaction
from django.db.models.signals import post_save

from celery.decorators import task
from multidb.pinning import pin_this_thread, unpin_this_thread

from activity.models import Action
from forums.models import Post


log = logging.getLogger('k.task')


@task
def log_reply(post):
    pin_this_thread()

    creator = post.author  # TODO: Rename post.author to post.creator.
    created = post.created
    thread = post.thread
    users = [p.author for p in
             thread.post_set.select_related('author').exclude(author=creator)]
    users = set(users)  # Remove duplicates.

    if users:
        action = Action.objects.create(
            creator=creator,
            created=created,
            url=post.get_absolute_url(),
            content_object=post,
            formatter_cls='forums.formatters.ForumReplyFormatter')
        action.users.add(*users)

    transaction.commit_unless_managed()
    unpin_this_thread()


@task
def index_threads(ids, **kw):
    log.debug('Indexing threads: %r', ids)
    from forums import es_search
    from forums.models import Thread
    for thread in Thread.uncached.filter(id__in=ids):
        es_search.index_thread(es_search.extract_thread(thread), refresh=True)


@task
def unindex_threads(ids, **kw):
    log.debug('Unindexing threads: %r', ids)
    from forums import es_search
    es_search.unindex_threads(ids)


def connector(sender, instance, created, **kw):
    if created:
        log_reply.delay(instance)

post_save.connect(connector, sender=Post, dispatch_uid='forum_post_activity')
