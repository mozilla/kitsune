from django.conf.urls import patterns, url, include


group_patterns = patterns('kitsune.groups.views',
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

urlpatterns = patterns('kitsune.groups.views',
    url(r'^$', 'list', name='groups.list'),
    url(r'^join-contributors$', 'join_contributors',
        name='groups.join_contributors'),
    (r'^/(?P<group_slug>[^/]+)', include(group_patterns)),
)
