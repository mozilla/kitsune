from django.conf.urls import url

from kitsune.search import views


urlpatterns = [
    url(r'^$', views.simple_search, name='search'),
    url(r'^/advanced$', views.advanced_search, name='search.advanced'),
    url(r'^/xml$', views.opensearch_plugin, name='search.plugin'),
    url(r'^/suggestions$', views.opensearch_suggestions, name='search.suggestions'),
]
