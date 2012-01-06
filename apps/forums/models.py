import datetime

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from tidings.models import NotificationsMixin

from access import has_perm, perm_is_defined_on
from activity.models import ActionMixin
import forums
from sumo.helpers import urlparams, wiki_to_html
from sumo.urlresolvers import reverse
from sumo.models import ModelBase
from search import searcher
from search.models import SearchMixin
from search.es_utils import (TYPE, ANALYZER, STORE, TERM_VECTOR, INTEGER,
                             STRING, BOOLEAN, DATE, YES, SNOWBALL,
                             WITH_POS_OFFSETS)
from search.utils import crc32
import waffle


def _last_post_from(posts, exclude_post=None):
    """Return the most recent post in the given set, excluding the given post.

    If there are none, return None.

    """
    if exclude_post:
        posts = posts.exclude(id=exclude_post.id)
    posts = posts.order_by('-created')
    try:
        return posts[0]
    except IndexError:
        return None


class ThreadLockedError(Exception):
    """Trying to create a post in a locked thread."""


class Forum(NotificationsMixin, ModelBase):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True)
    last_post = models.ForeignKey('Post', related_name='last_post_in_forum',
                                  null=True)

    class Meta(object):
        permissions = (
                ('view_in_forum',
                 'Can view restricted forums'),
                ('post_in_forum',
                 'Can post in restricted forums'))

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('forums.threads', kwargs={'forum_slug': self.slug})

    def allows_viewing_by(self, user):
        """Return whether a user can view me, my threads, and their posts."""
        return (self._allows_public_viewing() or
                has_perm(user, 'forums_forum.view_in_forum', self))

    def _allows_public_viewing(self):
        """Return whether I am a world-readable forum.

        If a django-authority permission relates to me, I am considered non-
        public. (We assume that you attached a permission to me in order to
        assign it to some users or groups.) Considered adding a Public flag to
        this model, but we didn't want it to show up on form and thus be
        accidentally flippable by readers of the Admin forum, who are all
        privileged enough to do so.

        """
        return not perm_is_defined_on('forums_forum.view_in_forum', self)

    def allows_posting_by(self, user):
        """Return whether a user can make threads and posts in me."""
        return (self._allows_public_posting() or
                has_perm(user, 'forums_forum.post_in_forum', self))

    def _allows_public_posting(self):
        """Return whether I am a world-writable forum."""
        return not perm_is_defined_on('forums_forum.post_in_forum', self)

    def update_last_post(self, exclude_thread=None, exclude_post=None):
        """Set my last post to the newest, excluding given thread and post."""
        posts = Post.objects.filter(thread__forum=self)
        if exclude_thread:
            posts = posts.exclude(thread=exclude_thread)
        self.last_post = _last_post_from(posts, exclude_post=exclude_post)


class Thread(NotificationsMixin, ModelBase, SearchMixin):
    title = models.CharField(max_length=255)
    forum = models.ForeignKey('Forum')
    created = models.DateTimeField(default=datetime.datetime.now,
                                   db_index=True)
    creator = models.ForeignKey(User)
    last_post = models.ForeignKey('Post', related_name='last_post_in',
                                  null=True)
    replies = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    is_sticky = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-is_sticky', '-last_post__created']

    def __setattr__(self, attr, val):
        """Notice when the forum field changes.

        A property won't do here, because it usurps the "forum" name and
        prevents us from using lookups like Thread.objects.filter(forum=f).

        """
        # When http://code.djangoproject.com/ticket/3148 adds nice getter and
        # setter hooks, use those instead.
        if attr == 'forum' and not hasattr(self, '_old_forum'):
            try:
                old = self.forum
            except AttributeError:  # When making a new Thread(forum=3), the
                pass                # forum attr doesn't exist yet.
            else:
                self._old_forum = old
        super(Thread, self).__setattr__(attr, val)

    @property
    def last_page(self):
        """Returns the page number for the last post."""
        return self.replies / forums.POSTS_PER_PAGE + 1

    def __unicode__(self):
        return self.title

    def delete(self, *args, **kwargs):
        """Override delete method to update parent forum info."""
        forum = Forum.uncached.get(pk=self.forum.id)
        if forum.last_post and forum.last_post.thread_id == self.id:
            forum.update_last_post(exclude_thread=self)
            forum.save()

        super(Thread, self).delete(*args, **kwargs)

    def new_post(self, author, content):
        """Create a new post, if the thread is unlocked."""
        if self.is_locked:
            raise ThreadLockedError

        return self.post_set.create(author=author, content=content)

    def get_absolute_url(self):
        return reverse('forums.posts', args=[self.forum.slug, self.id])

    def get_last_post_url(self):
        query = {'last': self.last_post_id}
        page = self.last_page
        if page > 1:
            query['page'] = page
        url = reverse('forums.posts', args=[self.forum.slug, self.id])
        return urlparams(url, hash='post-%s' % self.last_post_id, **query)

    def save(self, *args, **kwargs):
        super(Thread, self).save(*args, **kwargs)
        old_forum = getattr(self, '_old_forum', None)
        new_forum = self.forum
        if old_forum and old_forum != new_forum:
            old_forum.update_last_post(exclude_thread=self)
            old_forum.save()
            new_forum.update_last_post()
            new_forum.save()
            del self._old_forum

    def update_last_post(self, exclude_post=None):
        """Set my last post to the newest, excluding the given post."""
        last = _last_post_from(self.post_set, exclude_post=exclude_post)
        self.last_post = last
        # If self.last_post is None, and this was called from Post.delete,
        # then Post.delete will erase the thread, as well.

    @classmethod
    def get_mapping(cls):
        mapping = {
            'properties': {
                'id': {TYPE: INTEGER},
                'thread_id': {TYPE: INTEGER},
                'forum_id': {TYPE: INTEGER},
                'title': {TYPE: STRING, ANALYZER: SNOWBALL},
                'is_sticky': {TYPE: BOOLEAN},
                'is_locked': {TYPE: BOOLEAN},
                'author_id': {TYPE: INTEGER},
                'author_ord': {TYPE: STRING},
                'content': {TYPE: STRING, ANALYZER: SNOWBALL,
                            STORE: YES, TERM_VECTOR: WITH_POS_OFFSETS},
                'created': {TYPE: DATE},
                'updated': {TYPE: DATE},
                'replies': {TYPE: INTEGER}
                }
            }
        return mapping

    def extract_document(self):
        """Extracts interesting thing from a Thread and its Posts"""
        d = {}
        d['id'] = self.id
        d['forum_id'] = self.forum.id
        d['title'] = self.title
        d['is_sticky'] = self.is_sticky
        d['is_locked'] = self.is_locked
        d['created'] = self.created

        if self.last_post is not None:
            d['updated'] = self.last_post.created
        else:
            d['updates'] = None

        d['replies'] = self.replies

        author_ids = set()
        author_ords = set()
        content = []

        for post in self.post_set.all():
            author_ids.add(post.author.id)
            author_ords.add(post.author.username)
            content.append(post.content)

        d['author_id'] = list(author_ids)
        d['author_ord'] = list(author_ords)
        d['content'] = content

        return d


# Register this as a model we index in ES.
Thread.register_search_model()


def _update_t_index(sender, instance, **kw):
    """Given a Thread, creates an index task"""
    if not kw.get('raw'):
        obj = instance
        obj.__class__.add_index_task((obj.id,))


def _remove_t_index(sender, instance, **kw):
    """Given a Thread, create an unindex task"""
    if not kw.get('raw'):
        obj = instance
        obj.__class__.add_unindex_task((obj.id,))


f_t_es_post_save = receiver(
    post_save, sender=Thread,
    dispatch_uid='f.t.es.post_save')(_update_t_index)
f_t_es_pre_delete = receiver(
    pre_delete, sender=Thread,
    dispatch_uid='f.t.es.pre_delete')(_remove_t_index)


class Post(ActionMixin, ModelBase):
    thread = models.ForeignKey('Thread')
    content = models.TextField()
    author = models.ForeignKey(User)
    created = models.DateTimeField(default=datetime.datetime.now,
                                   db_index=True)
    updated = models.DateTimeField(default=datetime.datetime.now,
                                   db_index=True)
    updated_by = models.ForeignKey(User,
                                   related_name='post_last_updated_by',
                                   null=True)

    class Meta:
        ordering = ['created']

    class SphinxMeta(object):
        index = 'discussion_forums'
        filter_mapping = {'author_ord': crc32}

    def __unicode__(self):
        return self.content[:50]

    def save(self, *args, **kwargs):
        """
        Override save method to update parent thread info and take care of
        created and updated.
        """
        new = self.id is None

        if not new:
            self.updated = datetime.datetime.now()

        super(Post, self).save(*args, **kwargs)

        if new:
            self.thread.replies = self.thread.post_set.count() - 1
            self.thread.last_post = self
            self.thread.save()

            self.thread.forum.last_post = self
            self.thread.forum.save()

    def delete(self, *args, **kwargs):
        """Override delete method to update parent thread info."""
        thread = Thread.uncached.get(pk=self.thread.id)
        if thread.last_post_id and thread.last_post_id == self.id:
            thread.update_last_post(exclude_post=self)
        thread.replies = thread.post_set.count() - 2
        thread.save()

        forum = Forum.uncached.get(pk=thread.forum.id)
        if forum.last_post_id and forum.last_post_id == self.id:
            forum.update_last_post(exclude_post=self)
            forum.save()

        super(Post, self).delete(*args, **kwargs)
        # If I was the last post in the thread, delete the thread.
        if thread.last_post is None:
            thread.delete()

    @property
    def page(self):
        """Get the page of the thread on which this post is found."""
        t = self.thread
        earlier = t.post_set.filter(created__lte=self.created).count() - 1
        if earlier < 1:
            return 1
        return earlier / forums.POSTS_PER_PAGE + 1

    def get_absolute_url(self):
        query = {}
        if self.page > 1:
            query = {'page': self.page}

        url_ = self.thread.get_absolute_url()
        return urlparams(url_, hash='post-%s' % self.id, **query)

    @property
    def content_parsed(self):
        return wiki_to_html(self.content)


def _update_post_index(sender, instance, **kw):
    """Given a Post, update the Thread in the index"""
    if not kw.get('raw'):
        obj = instance.thread
        obj.__class__.add_index_task((obj.id,))


f_p_es_post_save = receiver(
    post_save, sender=Post,
    dispatch_uid='f_p_es_post_save')(_update_post_index)
f_p_es_pre_delete = receiver(
    pre_delete, sender=Post,
    dispatch_uid='f_p_es_pre_delete')(_update_post_index)


def discussion_searcher(request):
    """Return a forum searcher with default parameters."""
    if waffle.flag_is_active(request, 'elasticsearch'):
        index_model = Thread
    else:
        # The index is on Post but with the Thread.title for the
        # Thread related to the Post. We base the S off Post because
        # we need to excerpt content.
        index_model = Post

    return (searcher(request)(index_model).weight(title=2, content=1)
                                          .group_by('thread_id', '-@group')
                                          .query_fields('title__text',
                                                        'content__text')
                                          .order_by('created'))
