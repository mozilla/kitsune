from django.conf.urls import url

from kitsune.kbadge import views


urlpatterns = [
    url(r"^$", views.BadgesListView.as_view(), name="kbadge.badges_list"),
    url(r"^awards/?$", views.AwardsListView.as_view(), name="kbadge.awards_list"),
    url(
        r"^badge/(?P<slug>[^/]+)/awards/(?P<id>\d+)/?$",
        views.award_detail,
        name="kbadge.award_detail",
    ),
    url(r"^badge/(?P<slug>[^/]+)/?$", views.detail, name="kbadge.badge_detail"),
]
