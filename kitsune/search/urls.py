from django.conf.urls import url, include

from kitsune.search import views


urlpatterns = [
    url(r"^$", views.simple_search, name="search"),
    url(r"^/advanced$", views.advanced_search, name="search.advanced"),
    url(r"^/xml$", views.opensearch_plugin, name="search.plugin"),
    url(r"^/suggestions$", views.opensearch_suggestions, name="search.suggestions"),
    url(r"^/v2/", include("kitsune.search.v2.urls")),
]
