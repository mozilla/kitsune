from django.conf.urls import patterns, url


urlpatterns = patterns('kitsune.topics.views',
    url(r'^/(?P<slug>[^/]+)$', 'topic_landing', name='topics.topic'),
)
