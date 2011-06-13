from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('groups.views',
    url(r'^$', 'list', name='groups.list'),
    url(r'^/(?P<group_slug>[^/]+)$', 'profile', name='groups.profile'),
    url(r'^/(?P<group_slug>[^/]+)/edit$', 'edit', name='groups.edit'),
    url(r'^/(?P<group_slug>[^/]+)/avatar$', 'edit_avatar',
        name='groups.edit_avatar'),
    url(r'^/(?P<group_slug>[^/]+)/avatar/delete$', 'delete_avatar',
        name='groups.delete_avatar'),
)
