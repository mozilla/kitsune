from django.conf.urls import patterns, url


urlpatterns = patterns(
    'kitsune.community.views',
    url(r'^$', 'home', name='community.home'),
    url(r'^/search$', 'search', name='community.search'),
    url(r'^/top-contributors/(?P<area>[\w-]+)$', 'top_contributors',
    	name='community.top_contributors'),
)
