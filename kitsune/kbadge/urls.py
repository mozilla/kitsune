from django.urls import re_path

from kitsune.kbadge import views

urlpatterns = [
    re_path(r"^$", views.badges_list, name="kbadge.badges_list"),
    re_path(r"^awards/?$", views.awards_list, name="kbadge.awards_list"),
    re_path(
        r"^badge/(?P<slug>[^/]+)/awards/(?P<id>\d+)/?$",
        views.award_detail,
        name="kbadge.award_detail",
    ),
    re_path(r"^badge/(?P<slug>[^/]+)/?$", views.detail, name="kbadge.badge_detail"),
]
