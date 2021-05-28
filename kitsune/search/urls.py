from django.conf.urls import url

from kitsune.search import views

urlpatterns = [
    url(r"^$", views.simple_search, name="search"),
    url(r"^/xml$", views.opensearch_plugin, name="search.plugin"),
]
