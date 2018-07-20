from django.conf.urls import url, include

from kitsune.groups import views


group_patterns = [
    url(r'^$', views.profile, name='groups.profile'),
    url(r'^/edit$', views.edit, name='groups.edit'),
    url(r'^/avatar$', views.edit_avatar, name='groups.edit_avatar'),
    url(r'^/avatar/delete$', views.delete_avatar, name='groups.delete_avatar'),
    url(r'^/add-member$', views.add_member, name='groups.add_member'),
    url(r'^/remove-member/(?P<user_id>\d+)$', views.remove_member,
        name='groups.remove_member'),
    url(r'^/add-leader$', views.add_leader, name='groups.add_leader'),
    url(r'^/remove-leader/(?P<user_id>\d+)$', views.remove_leader,
        name='groups.remove_leader'),
]

urlpatterns = [
    url(r'^$', views.list, name='groups.list'),
    url(r'^/join-contributors$', views.join_contributors,
        name='groups.join_contributors'),
    url(r'^/(?P<group_slug>[^/]+)', include(group_patterns)),
]
