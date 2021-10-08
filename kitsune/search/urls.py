from django.urls import path

from kitsune.search import views

urlpatterns = [
    path("", views.simple_search, name="search"),
    path("xml", views.opensearch_plugin, name="search.plugin"),
]
