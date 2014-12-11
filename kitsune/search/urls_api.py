from django.conf.urls import patterns, url

from kitsune.search import api

# API urls. Prefixed with /api/2/
urlpatterns = patterns(
    '',
    url('^search/suggest/$', api.suggest, name='search.suggest'),
)
