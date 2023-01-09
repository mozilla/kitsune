from django.conf import settings
from django.urls import re_path

from kitsune.flagit import views as flagit_views
from kitsune.kbforums import views
from kitsune.kbforums.feeds import PostsFeed, ThreadsFeed
from kitsune.kbforums.models import Post
from kitsune.sumo.views import handle404

if settings.DISABLE_FEEDS:
    threads_feed_view = handle404
    posts_feed_view = handle404
else:
    threads_feed_view = ThreadsFeed()
    posts_feed_view = PostsFeed()

# These patterns inherit from /document/discuss
urlpatterns = [
    re_path(r"^$", views.threads, name="wiki.discuss.threads"),
    re_path(r"^feed", threads_feed_view, name="wiki.discuss.threads.feed"),
    re_path(r"^new", views.new_thread, name="wiki.discuss.new_thread"),
    re_path(r"^watch", views.watch_forum, name="wiki.discuss.watch_forum"),
    re_path(
        r"^post-preview-async$", views.post_preview_async, name="wiki.discuss.post_preview_async"
    ),
    re_path(r"^(?P<thread_id>\d+)$", views.posts, name="wiki.discuss.posts"),
    re_path(r"^(?P<thread_id>\d+)/feed$", posts_feed_view, name="wiki.discuss.posts.feed"),
    re_path(r"^(?P<thread_id>\d+)/watch$", views.watch_thread, name="wiki.discuss.watch_thread"),
    re_path(r"^(?P<thread_id>\d+)/reply$", views.reply, name="wiki.discuss.reply"),
    re_path(
        r"^(?P<thread_id>\d+)/sticky$", views.sticky_thread, name="wiki.discuss.sticky_thread"
    ),
    re_path(r"^(?P<thread_id>\d+)/lock$", views.lock_thread, name="wiki.discuss.lock_thread"),
    re_path(r"^(?P<thread_id>\d+)/edit$", views.edit_thread, name="wiki.discuss.edit_thread"),
    re_path(
        r"^(?P<thread_id>\d+)/delete$", views.delete_thread, name="wiki.discuss.delete_thread"
    ),
    re_path(
        r"^(?P<thread_id>\d+)/(?P<post_id>\d+)/edit",
        views.edit_post,
        name="wiki.discuss.edit_post",
    ),
    re_path(
        r"^(?P<thread_id>\d+)/(?P<post_id>\d+)/delete",
        views.delete_post,
        name="wiki.discuss.delete_post",
    ),
    # Flag discussion posts
    re_path(
        r"^(?P<object_id>\d+)/flag$",
        flagit_views.flag,
        {"model": Post},
        name="wiki.discuss.flag_post",
    ),
]
