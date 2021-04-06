from django.conf import settings
from django.conf.urls import include
from django.urls import path

from kitsune.flagit import views as flagit_views
from kitsune.forums import views
from kitsune.forums.feeds import PostsFeed, ThreadsFeed
from kitsune.forums.models import Post
from kitsune.sumo.views import handle404

if settings.DISABLE_FEEDS:
    threads_feed_view = handle404
    posts_feed_view = handle404
else:
    threads_feed_view = ThreadsFeed()
    posts_feed_view = PostsFeed()

# These patterns inherit (?P<forum_slug>\d+).
forum_patterns = [
    path("", views.threads, name="forums.threads"),
    path("new/", views.new_thread, name="forums.new_thread"),
    path("<int:thread_id>/", views.posts, name="forums.posts"),
    path("<int:thread_id>/reply/", views.reply, name="forums.reply"),
    path("feed/", threads_feed_view, name="forums.threads.feed"),
    path("<int:thread_id>/feed/", posts_feed_view, name="forums.posts.feed"),
    path("<int:thread_id>/lock/", views.lock_thread, name="forums.lock_thread"),
    path("<int:thread_id>/sticky/", views.sticky_thread, name="forums.sticky_thread"),
    path("<int:thread_id>/edit/", views.edit_thread, name="forums.edit_thread"),
    path("<int:thread_id>/delete/", views.delete_thread, name="forums.delete_thread"),
    path("<int:thread_id>/move/", views.move_thread, name="forums.move_thread"),
    path("<int:thread_id>/<int:post_id>/edit/", views.edit_post, name="forums.edit_post"),
    path(
        "<int:thread_id>/<int:post_id>/delete/",
        views.delete_post,
        name="forums.delete_post",
    ),
    path("<int:thread_id>/watch/", views.watch_thread, name="forums.watch_thread"),
    path("watch/", views.watch_forum, name="forums.watch_forum"),
    # Flag posts
    path(
        "<int:thread_id>/<int:object_id>/flag/",
        flagit_views.flag,
        {"model": Post},
        name="forums.flag_post",
    ),
]

urlpatterns = [
    path("", views.forums, name="forums.forums"),
    path("post-preview-async/", views.post_preview_async, name="forums.post_preview_async"),
    path("<slug:forum_slug>/", include(forum_patterns)),
]
