from django.conf.urls import url

from kitsune.search import api

# API urls. Prefixed with /api/2/
urlpatterns = [
    url("^search/suggest/$", api.suggest, name="search.suggest"),
]
