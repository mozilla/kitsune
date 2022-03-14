from django.urls import re_path

from kitsune.kbadge import views

urlpatterns = [
    re_path(r"^$", views.BadgesListView.as_view(), name="kbadge.badges_list"),
    re_path(r"^awards/?$", views.AwardsListView.as_view(), name="kbadge.awards_list"),
    re_path(
        r"^badge/(?P<slug>[^/]+)/awards/(?P<id>\d+)/?$",
        views.award_detail,
        name="kbadge.award_detail",
    ),
    re_path(r"^badge/(?P<slug>[^/]+)/?$", views.detail, name="kbadge.badge_detail"),
]
