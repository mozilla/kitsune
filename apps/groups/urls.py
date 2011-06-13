from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('groups.views',
    url(r'^$', 'list', name='groups.list'),
    url(r'^/(?P<group_slug>[^/]+)$', 'profile', name='groups.profile'),
    url(r'^/(?P<group_slug>[^/]+)/edit$', 'edit', name='groups.edit'),
)
