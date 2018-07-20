from django.conf import settings
from django.conf.urls import url, include

from kitsune.forums import views
from kitsune.forums.feeds import ThreadsFeed, PostsFeed
from kitsune.forums.models import Post
from kitsune.flagit import views as flagit_views
from kitsune.sumo.views import handle404


if settings.DISABLE_FEEDS:
    threads_feed_view = handle404
    posts_feed_view = handle404
else:
    threads_feed_view = ThreadsFeed()
    posts_feed_view = PostsFeed()

# These patterns inherit (?P<forum_slug>\d+).
forum_patterns = [
    url(r'^$', views.threads, name='forums.threads'),
    url(r'^/new$', views.new_thread, name='forums.new_thread'),
    url(r'^/(?P<thread_id>\d+)$', views.posts, name='forums.posts'),
    url(r'^/(?P<thread_id>\d+)/reply$', views.reply, name='forums.reply'),
    url(r'^/feed$', threads_feed_view, name="forums.threads.feed"),
    url(r'^/(?P<thread_id>\d+)/feed$', posts_feed_view, name="forums.posts.feed"),
    url(r'^/(?P<thread_id>\d+)/lock$', views.lock_thread,
        name='forums.lock_thread'),
    url(r'^/(?P<thread_id>\d+)/sticky$', views.sticky_thread,
        name='forums.sticky_thread'),
    url(r'^/(?P<thread_id>\d+)/edit$', views.edit_thread,
        name='forums.edit_thread'),
    url(r'^/(?P<thread_id>\d+)/delete$', views.delete_thread,
        name='forums.delete_thread'),
    url(r'^/(?P<thread_id>\d+)/move$', views.move_thread,
        name='forums.move_thread'),
    url(r'^/(?P<thread_id>\d+)/(?P<post_id>\d+)/edit$', views.edit_post,
        name='forums.edit_post'),
    url(r'^/(?P<thread_id>\d+)/(?P<post_id>\d+)/delete$', views.delete_post,
        name='forums.delete_post'),
    url(r'^/(?P<thread_id>\d+)/watch', views.watch_thread,
        name='forums.watch_thread'),
    url(r'^/watch', views.watch_forum, name='forums.watch_forum'),

    # Flag posts
    url(r'^/(?P<thread_id>\d+)/(?P<object_id>\d+)/flag$', flagit_views.flag,
        {'model': Post}, name='forums.flag_post'),
]

urlpatterns = [
    url(r'^$', views.forums, name='forums.forums'),
    url(r'^/post-preview-async$', views.post_preview_async,
        name='forums.post_preview_async'),
    url(r'^/(?P<forum_slug>[\w\-]+)', include(forum_patterns)),
]
