from django.urls import re_path

from kitsune.community import views

urlpatterns = [
    re_path(r"^$", views.home, name="community.home"),
    re_path(r"^search$", views.search, name="community.search"),
    re_path(r"^metrics$", views.metrics, name="community.metrics"),
    re_path(
        r"^top-contributors/(?P<area>[\w-]+)$",
        views.top_contributors,
        name="community.top_contributors",
    ),
]
