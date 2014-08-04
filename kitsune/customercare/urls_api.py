from django.conf.urls import patterns, url

from kitsune.customercare import api


# API urls
urlpatterns = patterns(
    '',
    url(r'^banned$', api.BannedList.as_view()),
    url(r'^ban$', api.ban),
    url(r'^unban$', api.unban),
)
