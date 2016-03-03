from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _lazy

from tidings.events import InstanceEvent, EventUnion, Event

from kitsune.kbforums.models import Thread
from kitsune.sumo.email_utils import emails_with_users_and_watches
from kitsune.sumo.templatetags.jinja_helpers import add_utm
from kitsune.wiki.models import Document


def new_post_mails(reply, users_and_watches):
    """Return an interable of EmailMessages to send when a new post is
    created."""
    post_url = add_utm(reply.get_absolute_url(), 'kbforums-post')

    c = {'post': reply.content,
         'post_html': reply.content_parsed,
         'author': reply.creator,
         'host': Site.objects.get_current().domain,
         'thread': reply.thread.title,
         'forum': reply.thread.document.title,
         'post_url': post_url}

    return emails_with_users_and_watches(
        subject=_lazy(u'Re: {forum} - {thread}'),
        text_template='kbforums/email/new_post.ltxt',
        html_template='kbforums/email/new_post.html',
        context_vars=c,
        users_and_watches=users_and_watches)


def new_thread_mails(post, users_and_watches):
    """Return an interable of EmailMessages to send when a new thread is
    created."""
    post_url = add_utm(post.thread.get_absolute_url(), 'kbforums-thread')

    c = {'post': post.content,
         'post_html': post.content_parsed,
         'author': post.creator,
         'host': Site.objects.get_current().domain,
         'thread': post.thread.title,
         'forum': post.thread.document.title,
         'post_url': post_url}

    return emails_with_users_and_watches(
        subject=_lazy(u'{forum} - {thread}'),
        text_template='kbforums/email/new_thread.ltxt',
        html_template='kbforums/email/new_thread.html',
        context_vars=c,
        users_and_watches=users_and_watches)


class NewPostEvent(InstanceEvent):
    """An event which fires when a thread receives a reply"""

    event_type = 'kbthread reply'
    content_type = Thread

    def __init__(self, reply):
        super(NewPostEvent, self).__init__(reply.thread)
        # Need to store the reply for _mails
        self.reply = reply

    def fire(self, **kwargs):
        """Notify watchers of this thread, of the document, and of the
        locale."""
        return EventUnion(self, NewThreadEvent(self.reply),
                          NewPostInLocaleEvent(self.reply)).fire(**kwargs)

    def _mails(self, users_and_watches):
        return new_post_mails(self.reply, users_and_watches)


class NewThreadEvent(InstanceEvent):
    """An event which fires when a new thread is added to a kbforum"""

    event_type = 'kbforum thread'
    content_type = Document

    def __init__(self, post):
        super(NewThreadEvent, self).__init__(post.thread.document)
        # Need to store the post for _mails
        self.post = post

    def fire(self, **kwargs):
        """Notify watches of the document and of the locale."""
        return EventUnion(self, NewThreadEvent(self.post),
                          NewThreadInLocaleEvent(self.post)).fire(**kwargs)

    def _mails(self, users_and_watches):
        return new_thread_mails(self.post, users_and_watches)


class _NewActivityInLocaleEvent(Event):
    filters = set(['locale'])

    def __init__(self, locale):
        super(_NewActivityInLocaleEvent, self).__init__()
        self.locale = locale

    def _users_watching(self, **kwargs):
        return self._users_watching_by_filter(locale=self.locale, **kwargs)


class NewPostInLocaleEvent(_NewActivityInLocaleEvent):
    """Event fired when there is a new reply in a locale."""
    event_type = 'kbthread reply in locale'

    def __init__(self, reply):
        super(NewPostInLocaleEvent, self).__init__(
            reply.thread.document.locale)
        # Need to store the reply for _mails
        self.reply = reply

    def _mails(self, users_and_watches):
        return new_post_mails(self.reply, users_and_watches)


class NewThreadInLocaleEvent(_NewActivityInLocaleEvent):
    """Event fired when there is a new reply in a locale."""
    event_type = 'kbforum thread in locale'

    def __init__(self, post):
        super(NewThreadInLocaleEvent, self).__init__(
            post.thread.document.locale)
        # Need to store the post for _mails
        self.post = post

    def _mails(self, users_and_watches):
        return new_thread_mails(self.post, users_and_watches)
