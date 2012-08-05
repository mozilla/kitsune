from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('topics.views',
    url(r'^/(?P<slug>[^/]+)$', 'topic_landing', name='topics.topic'),
)
