import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from kitsune import forums
from kitsune.access.utils import has_perm
from kitsune.flagit.models import FlaggedObject
from kitsune.sumo.models import ModelBase
from kitsune.sumo.templatetags.jinja_helpers import urlparams, wiki_to_html
from kitsune.sumo.urlresolvers import reverse
from kitsune.tidings.models import NotificationsMixin


def _last_post_from(posts, exclude_post=None):
    """Return the most recent post in the given set, excluding the given post.

    If there are none, return None.

    """
    if exclude_post:
        posts = posts.exclude(id=exclude_post.id)
    posts = posts.order_by("-created")
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
    last_post = models.ForeignKey(
        "Post", related_name="last_post_in_forum", null=True, on_delete=models.SET_NULL
    )

    # Dictates the order in which forums are displayed in the forum list.
    display_order = models.IntegerField(default=1, db_index=True)

    # Whether or not this forum is visible in the forum list.
    is_listed = models.BooleanField(default=True, db_index=True)

    # Can only users/groups with permission view this forum?
    restrict_viewing = models.BooleanField(default=False, db_index=True)
    # Can only users/groups with permission post to this forum?
    restrict_posting = models.BooleanField(default=False, db_index=True)

    class Meta(object):
        ordering = ["display_order", "id"]
        permissions = (
            ("view_in_forum", "Can view restricted forums"),
            ("post_in_forum", "Can post in restricted forums"),
            ("delete_forum_thread", "Can delete forum threads"),
            ("edit_forum_thread", "Can edit forum threads"),
            ("lock_forum_thread", "Can lock/unlock forum threads"),
            ("move_forum_thread", "Can move threads between forums"),
            ("sticky_forum_thread", "Can mark/unmark a forum thread as sticky"),
            ("delete_forum_thread_post", "Can delete posts within forum threads"),
            ("edit_forum_thread_post", "Can edit posts within forum threads"),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("forums.threads", kwargs={"forum_slug": self.slug})

    def allows_viewing_by(self, user):
        """Return whether a user can view me, my threads, and their posts."""
        return (not self.restrict_viewing) or has_perm(user, "forums.view_in_forum", self)

    def allows_posting_by(self, user):
        """Return whether a user can make threads and posts in me."""
        return (not self.restrict_posting) or has_perm(user, "forums.post_in_forum", self)

    def update_last_post(self, exclude_thread=None, exclude_post=None):
        """Set my last post to the newest, excluding given thread and post."""
        posts = Post.objects.filter(thread__forum=self)
        if exclude_thread:
            posts = posts.exclude(thread=exclude_thread)
        self.last_post = _last_post_from(posts, exclude_post=exclude_post)

    @classmethod
    def authorized_forums_for_user(cls, user):
        """Returns the forums this user is authorized to view"""
        return [f for f in Forum.objects.all() if f.allows_viewing_by(user)]


class Thread(NotificationsMixin, ModelBase):
    title = models.CharField(max_length=255)
    forum = models.ForeignKey("Forum", on_delete=models.CASCADE)
    created = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    last_post = models.ForeignKey(
        "Post", related_name="last_post_in", null=True, on_delete=models.SET_NULL
    )
    replies = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    is_sticky = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-is_sticky", "-last_post__created"]

    def __setattr__(self, attr, val):
        """Notice when the forum field changes.

        A property won't do here, because it usurps the "forum" name and
        prevents us from using lookups like Thread.objects.filter(forum=f).

        """
        if attr == "forum" and not hasattr(self, "_old_forum"):
            try:
                self._old_forum = self.forum
            except ObjectDoesNotExist:
                pass
        super(Thread, self).__setattr__(attr, val)

    @property
    def last_page(self):
        """Returns the page number for the last post."""
        return self.replies // forums.POSTS_PER_PAGE + 1

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        """Override delete method to update parent forum info."""
        forum = Forum.objects.get(pk=self.forum.id)
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
        return reverse("forums.posts", args=[self.forum.slug, self.id])

    def get_last_post_url(self):
        query = {"last": self.last_post_id}
        page = self.last_page
        if page > 1:
            query["page"] = page
        url = reverse("forums.posts", args=[self.forum.slug, self.id])
        return urlparams(url, hash="post-%s" % self.last_post_id, **query)

    def save(self, *args, **kwargs):
        super(Thread, self).save(*args, **kwargs)
        old_forum = getattr(self, "_old_forum", None)
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


class Post(ModelBase):
    thread = models.ForeignKey("Thread", on_delete=models.CASCADE)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    updated = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="post_last_updated_by", null=True
    )
    flags = GenericRelation(FlaggedObject)

    updated_column_name = "updated"

    class Meta:
        ordering = ["created"]

    def __str__(self):
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
        thread = Thread.objects.get(pk=self.thread.id)
        if thread.last_post_id and thread.last_post_id == self.id:
            thread.update_last_post(exclude_post=self)
        thread.replies = thread.post_set.count() - 2
        thread.save()

        forum = Forum.objects.get(pk=thread.forum.id)
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
        return earlier // forums.POSTS_PER_PAGE + 1

    def get_absolute_url(self):
        query = {}
        if self.page > 1:
            query = {"page": self.page}

        url_ = self.thread.get_absolute_url()
        return urlparams(url_, hash="post-%s" % self.id, **query)

    @property
    def content_parsed(self):
        return wiki_to_html(self.content)
