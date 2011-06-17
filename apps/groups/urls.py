from django.conf.urls.defaults import patterns, url, include


group_patterns = patterns('groups.views',
    url(r'^$', 'profile', name='groups.profile'),
    url(r'^/edit$', 'edit', name='groups.edit'),
    url(r'^/avatar$', 'edit_avatar', name='groups.edit_avatar'),
    url(r'^/avatar/delete$', 'delete_avatar', name='groups.delete_avatar'),
    url(r'^/avatar$', 'edit_avatar', name='groups.edit_avatar'),
    url(r'^/add-member$', 'add_member', name='groups.add_member'),
    url(r'^/remove-member/(?P<user_id>\d+)$', 'remove_member',
        name='groups.remove_member'),
    url(r'^/add-leader$', 'add_leader', name='groups.add_leader'),
    url(r'^/remove-leader/(?P<user_id>\d+)$', 'remove_leader',
        name='groups.remove_leader'),
)

urlpatterns = patterns('groups.views',
    url(r'^$', 'list', name='groups.list'),
    (r'^/(?P<group_slug>[^/]+)', include(group_patterns)),
)
