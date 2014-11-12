from django.conf.urls import patterns, url


urlpatterns = patterns(
    'kitsune.search.views',
    url(r'^$', 'simple_search', name='search'),
    url(r'^/advanced$', 'advanced_search', name='search.advanced'),
    url(r'^/xml$', 'plugin', name='search.plugin'),
    url(r'^/suggestions$', 'suggestions', name='search.suggestions'),
)
