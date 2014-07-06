from django.conf.urls import patterns, url, include
from django.contrib.contenttypes.models import ContentType

from kitsune.forums.feeds import ThreadsFeed, PostsFeed
from kitsune.forums.models import Post
from kitsune.flagit import views as flagit_views


# These patterns inherit (?P<forum_slug>\d+).
forum_patterns = patterns(
    'kitsune.forums.views',
    url(r'^$', 'threads', name='forums.threads'),
    url(r'^/new$', 'new_thread', name='forums.new_thread'),
    url(r'^/(?P<thread_id>\d+)$', 'posts', name='forums.posts'),
    url(r'^/(?P<thread_id>\d+)/reply$', 'reply', name='forums.reply'),
    url(r'^/feed$', ThreadsFeed(), name="forums.threads.feed"),
    url(r'^/(?P<thread_id>\d+)/feed$', PostsFeed(), name="forums.posts.feed"),
    url(r'^/(?P<thread_id>\d+)/lock$', 'lock_thread',
        name='forums.lock_thread'),
    url(r'^/(?P<thread_id>\d+)/sticky$', 'sticky_thread',
        name='forums.sticky_thread'),
    url(r'^/(?P<thread_id>\d+)/edit$', 'edit_thread',
        name='forums.edit_thread'),
    url(r'^/(?P<thread_id>\d+)/delete$', 'delete_thread',
        name='forums.delete_thread'),
    url(r'^/(?P<thread_id>\d+)/move$', 'move_thread',
        name='forums.move_thread'),
    url(r'^/(?P<thread_id>\d+)/(?P<post_id>\d+)/edit$', 'edit_post',
        name='forums.edit_post'),
    url(r'^/(?P<thread_id>\d+)/(?P<post_id>\d+)/delete$', 'delete_post',
        name='forums.delete_post'),
    url(r'^/(?P<thread_id>\d+)/watch', 'watch_thread',
        name='forums.watch_thread'),
    url(r'^/watch', 'watch_forum', name='forums.watch_forum'),

    # Flag posts
    url(r'^/(?P<thread_id>\d+)/(?P<object_id>\d+)/flag$', flagit_views.flag,
        {'content_type': ContentType.objects.get_for_model(Post).id},
        name='forums.flag_post'),
)

urlpatterns = patterns(
    'kitsune.forums.views',
    url(r'^$', 'forums', name='forums.forums'),
    url(r'^/post-preview-async$', 'post_preview_async',
        name='forums.post_preview_async'),
    (r'^/(?P<forum_slug>[\w\-]+)', include(forum_patterns)),
)
