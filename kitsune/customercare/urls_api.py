from django.conf.urls import patterns, url

from kitsune.customercare import api


# API urls
urlpatterns = patterns(
    '',
    url(r'^banned$', api.BannedList.as_view(), name='customercare.api.banned'),
    url(r'^ban$', api.ban, name='customercare.api.ban'),
    url(r'^unban$', api.unban, name='customercare.api.unban'),
)
