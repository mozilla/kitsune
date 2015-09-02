from django.conf.urls import patterns, url


urlpatterns = patterns(
    'kitsune.coolsearch.views',
    url(r'^$', 'search', name='coolsearch.search'),
)
