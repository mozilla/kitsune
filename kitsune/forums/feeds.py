from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import Atom1Feed
from django.utils.html import strip_tags, escape
from django.utils.translation import ugettext as _

from kitsune import forums as constants
from kitsune.forums.models import Forum, Thread
from kitsune.sumo.feeds import Feed


class ThreadsFeed(Feed):
    feed_type = Atom1Feed

    def get_object(self, request, forum_slug):
        return get_object_or_404(Forum, slug=forum_slug)

    def title(self, forum):
        return _('Recently updated threads in %s') % forum.name

    def link(self, forum):
        return forum.get_absolute_url()

    def description(self, forum):
        return forum.description

    def items(self, forum):
        return forum.thread_set.order_by(
            '-last_post__created')[:constants.THREADS_PER_PAGE]

    def item_title(self, item):
        return item.title

    def item_author_name(self, item):
        return item.creator

    def item_pubdate(self, item):
        return item.created


class PostsFeed(Feed):
    feed_type = Atom1Feed

    def get_object(self, request, forum_slug, thread_id):
        return get_object_or_404(Thread, pk=thread_id)

    def title(self, thread):
        return _('Recent posts in %s') % thread.title

    def link(self, thread):
        return thread.get_absolute_url()

    def description(self, thread):
        return self.title(thread)

    def items(self, thread):
        return thread.post_set.order_by('-created')

    def item_title(self, item):
        return strip_tags(item.content_parsed)[:100]

    def item_description(self, item):
        return escape(item.content_parsed)

    def item_author_name(self, item):
        return item.author

    def item_pubdate(self, item):
        return item.created
