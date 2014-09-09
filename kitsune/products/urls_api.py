from django.conf.urls import patterns, url

from kitsune.products import api


# API urls
urlpatterns = patterns(
    '',
    url(r'^$', api.ProductList.as_view()),
    url(r'^(?P<product>[^/]+)/topic/?$', api.TopicList.as_view()),
    url(r'^(?P<product>[^/]+)/topic/(?P<topic>[^/]+)/?$',
        api.TopicDetail.as_view()),
)
