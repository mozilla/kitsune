from django.conf.urls import url

from kitsune.community import views


urlpatterns = [
    url(r"^$", views.home, name="community.home"),
    url(r"^/search$", views.search, name="community.search"),
    url(r"^/metrics$", views.metrics, name="community.metrics"),
    url(
        r"^/top-contributors/(?P<area>[\w-]+)$",
        views.top_contributors,
        name="community.top_contributors",
    ),
    url(
        r"^/top-contributors/(?P<area>[\w-]+)/new$",
        views.top_contributors_new,
        name="community.top_contributors_new",
    ),
]
