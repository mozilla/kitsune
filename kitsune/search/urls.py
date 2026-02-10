from django.conf import settings
from django.urls import re_path

from kitsune.search import api, views

urlpatterns = [
    re_path(r"^$", views.simple_search, name="search"),
    re_path(r"^xml$", views.opensearch_plugin, name="search.plugin"),
]

if settings.ENABLE_TESTING_ENDPOINTS:
    urlpatterns += [
        re_path(
            r"^api/reindex-document$",
            api.reindex_document,
            name="search.api.reindex_document",
        ),
    ]
