from django.urls import include, re_path

from kitsune.groups import views

group_patterns = [
    re_path(r"^$", views.profile, name="groups.profile"),
    re_path(r"^edit$", views.edit, name="groups.edit"),
    re_path(r"^avatar$", views.edit_avatar, name="groups.edit_avatar"),
    re_path(r"^avatar/delete$", views.delete_avatar, name="groups.delete_avatar"),
    re_path(r"^add-member$", views.add_member, name="groups.add_member"),
    re_path(r"^remove-member/(?P<user_id>\d+)$", views.remove_member, name="groups.remove_member"),
    re_path(r"^add-leader$", views.add_leader, name="groups.add_leader"),
    re_path(r"^remove-leader/(?P<user_id>\d+)$", views.remove_leader, name="groups.remove_leader"),
]

urlpatterns = [
    re_path(r"^$", views.list, name="groups.list"),
    re_path(r"^join-contributors$", views.join_contributors, name="groups.join_contributors"),
    re_path(r"^(?P<group_slug>[^/]+)/", include(group_patterns)),
]
