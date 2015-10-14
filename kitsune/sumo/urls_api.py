from django.conf.urls import patterns, url

from kitsune.sumo import api


# API urls
urlpatterns = patterns(
    '',

    url(r'^locales/$', api.locales_api_view, name='sumo.locales_api')
)
