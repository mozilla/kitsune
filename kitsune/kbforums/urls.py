from django.conf import settings
from django.conf.urls import url

from kitsune.kbforums import views
from kitsune.kbforums.feeds import ThreadsFeed, PostsFeed
from kitsune.kbforums.models import Post
from kitsune.flagit import views as flagit_views
from kitsune.sumo.views import handle404


if settings.DISABLE_FEEDS:
    threads_feed_view = handle404
    posts_feed_view = handle404
else:
    threads_feed_view = ThreadsFeed()
    posts_feed_view = PostsFeed()

# These patterns inherit from /document/discuss
urlpatterns = [
    url(r"^$", views.threads, name="wiki.discuss.threads"),
    url(r"^/feed", threads_feed_view, name="wiki.discuss.threads.feed"),
    url(r"^/new", views.new_thread, name="wiki.discuss.new_thread"),
    url(r"^/watch", views.watch_forum, name="wiki.discuss.watch_forum"),
    url(
        r"^/post-preview-async$", views.post_preview_async, name="wiki.discuss.post_preview_async"
    ),
    url(r"^/(?P<thread_id>\d+)$", views.posts, name="wiki.discuss.posts"),
    url(r"^/(?P<thread_id>\d+)/feed$", posts_feed_view, name="wiki.discuss.posts.feed"),
    url(r"^/(?P<thread_id>\d+)/watch$", views.watch_thread, name="wiki.discuss.watch_thread"),
    url(r"^/(?P<thread_id>\d+)/reply$", views.reply, name="wiki.discuss.reply"),
    url(r"^/(?P<thread_id>\d+)/sticky$", views.sticky_thread, name="wiki.discuss.sticky_thread"),
    url(r"^/(?P<thread_id>\d+)/lock$", views.lock_thread, name="wiki.discuss.lock_thread"),
    url(r"^/(?P<thread_id>\d+)/edit$", views.edit_thread, name="wiki.discuss.edit_thread"),
    url(r"^/(?P<thread_id>\d+)/delete$", views.delete_thread, name="wiki.discuss.delete_thread"),
    url(
        r"^/(?P<thread_id>\d+)/(?P<post_id>\d+)/edit",
        views.edit_post,
        name="wiki.discuss.edit_post",
    ),
    url(
        r"^/(?P<thread_id>\d+)/(?P<post_id>\d+)/delete",
        views.delete_post,
        name="wiki.discuss.delete_post",
    ),
    # Flag discussion posts
    url(
        r"^/(?P<object_id>\d+)/flag$",
        flagit_views.flag,
        {"model": Post},
        name="wiki.discuss.flag_post",
    ),
]
