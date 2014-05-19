from django.conf.urls import patterns, url

from kitsune.wiki import api


# API urls
urlpatterns = patterns(
    '',
    url(r'^$', api.DocumentList.as_view()),
    url(r'^(?P<slug>[^/]+)$', api.DocumentDetail.as_view()),
)
