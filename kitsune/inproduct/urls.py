from django.conf.urls import url

from kitsune.inproduct import views


urlpatterns = [
    url(
        r"/(?P<product>[^/]+)/(?P<version>[^/]+)/(?P<platform>[^/]+)/"
        r"(?P<locale>[^/]+)(?:/(?P<topic>[^/]+))?/?",
        views.redirect,
        name="inproduct.redirect",
    ),
]
