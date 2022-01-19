from django.urls import re_path

from kitsune.inproduct import views

urlpatterns = [
    re_path(
        r"/(?P<product>[^/]+)/(?P<version>[^/]+)/(?P<platform>[^/]+)/"
        r"(?P<locale>[^/]+)(?:/(?P<topic>[^/]+))?/?",
        views.redirect,
        name="inproduct.redirect",
    ),
]
