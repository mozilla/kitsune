from django.conf.urls import patterns, url

from kitsune.gallery import api


# API urls
urlpatterns = patterns(
    '',
    url(r'^image/?$', api.ImageList.as_view()),
    url(r'^image/(?P<pk>\d+)/?$', api.ImageDetail.as_view()),
)
