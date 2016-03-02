from django.conf.urls import patterns, url


urlpatterns = patterns(
    'kitsune.community.views',
    url(r'^$', 'home', name='community.home'),
    url(r'^/search$', 'search', name='community.search'),
    url(r'^/metrics$', 'metrics', name='community.metrics'),
    url(r'^/top-contributors/(?P<area>[\w-]+)$', 'top_contributors',
        name='community.top_contributors'),
    url(r'^/top-contributors/(?P<area>[\w-]+)/new$', 'top_contributors_new',
        name='community.top_contributors_new'),
)
