from django.conf.urls import patterns, url

from kitsune.wiki import api


# API urls
urlpatterns = patterns(
    '',
    url(r'documents/?$', api.DocumentList.as_view()),
    url(r'documents/(?P<slug>[^/]+)$', api.DocumentDetail.as_view()),
)
