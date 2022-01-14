from django.urls import re_path

from kitsune.postcrash import views

urlpatterns = [
    re_path("^$", views.api, name="postcrash.api"),
]
