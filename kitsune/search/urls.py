from django.conf.urls import url

from kitsune.search import views
from kitsune.search.v2 import views as v2_views

urlpatterns = [
    url(r"^$", v2_views.simple_search, name="search"),
    url(r"^/xml$", views.opensearch_plugin, name="search.plugin"),
    url(r"^/suggestions$", views.opensearch_suggestions, name="search.suggestions"),
]
