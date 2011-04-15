from django.conf.urls.defaults import patterns, url

from sumo.views import deprecated_redirect

urlpatterns = patterns('',
  url(r'^/3', deprecated_redirect,
      {'url': 'forums.threads', 'forum_slug': 'contributors'}),
  url(r'^/4', deprecated_redirect,
      {'url': 'forums.threads', 'forum_slug': 'off-topic'}),
  url(r'^/5', deprecated_redirect,
      {'url': 'forums.threads', 'forum_slug': 'knowledge-base-articles'}),
)
