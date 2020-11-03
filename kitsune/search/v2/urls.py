from django.conf.urls import url

from kitsune.search.v2 import views


urlpatterns = [
    url(r"^$", views.simple_search, name="search.v2"),
]
