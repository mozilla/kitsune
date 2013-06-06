from django.conf.urls import patterns, url


urlpatterns = patterns('kitsune.search.views',
    url(r'^$', 'search', name='search'),
    url(r'^/xml$', 'plugin', name='search.plugin'),
    url(r'^/suggestions$', 'suggestions', name='search.suggestions'),
)
