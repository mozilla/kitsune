from django.conf.urls import patterns, url

from kitsune.products import api


# API urls
urlpatterns = patterns(
    '',
    url(r'^$', api.ProductList.as_view()),
    url(r'^(?P<slug>[^/]+)/topics$', api.TopicList.as_view()),
)
