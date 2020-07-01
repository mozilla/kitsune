from django.conf.urls import url

from kitsune.postcrash import views


urlpatterns = [
    url("^$", views.api, name="postcrash.api"),
]
