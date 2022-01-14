from django.urls import re_path

from kitsune.search import views

urlpatterns = [
    re_path(r"^$", views.simple_search, name="search"),
    re_path(r"^/xml$", views.opensearch_plugin, name="search.plugin"),
]
