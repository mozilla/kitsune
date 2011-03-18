from django.contrib.sites.models import Site

from tower import ugettext as _

from forums.models import Thread, Forum
from notifications.events import InstanceEvent, EventUnion
from notifications.utils import emails_with_users_and_watches


class NewPostEvent(InstanceEvent):
    """An event which fires when a thread receives a reply

    Firing this also notifies watchers of the containing forum.

    """
    event_type = 'thread reply'
    content_type = Thread

    def __init__(self, reply):
        super(NewPostEvent, self).__init__(reply.thread)
        # Need to store the reply for _mails
        self.reply = reply

    def fire(self, **kwargs):
        """Notify not only watchers of this thread but of the parent forum."""
        return EventUnion(self, NewThreadEvent(self.reply)).fire(**kwargs)

    def _mails(self, users_and_watches):
        c = {'post': self.reply.content, 'author': self.reply.author.username,
             'host': Site.objects.get_current().domain,
             'thread_title': self.instance.title,
             'post_url': self.reply.get_absolute_url()}

        return emails_with_users_and_watches(
            _(u'Reply to: %s') % self.reply.thread.title,
            'forums/email/new_post.ltxt',
            c,
            users_and_watches)


class NewThreadEvent(InstanceEvent):
    """An event which fires when a new thread is added to a forum"""

    event_type = 'forum thread'
    content_type = Forum

    def __init__(self, post):
        super(NewThreadEvent, self).__init__(post.thread.forum)
        # Need to store the post for _mails
        self.post = post

    def _mails(self, users_and_watches):
        subject = _(u'New thread in %s forum: %s') % (
            self.post.thread.forum.name, self.post.thread.title)
        c = {'post': self.post.content, 'author': self.post.author.username,
             'host': Site.objects.get_current().domain,
             'thread_title': self.post.thread.title,
             'post_url': self.post.thread.get_absolute_url()}

        return emails_with_users_and_watches(
            subject,
            'forums/email/new_thread.ltxt',
            c,
            users_and_watches)
