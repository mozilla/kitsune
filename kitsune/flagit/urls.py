from django.urls import re_path

from kitsune.flagit import views

urlpatterns = [
    re_path(r"^flagged$", views.flagged_queue, name="flagit.flagged_queue"),
    re_path(r"^flag$", views.flag, name="flagit.flag"),
    re_path(r"^update/(?P<flagged_object_id>\d+)$", views.update, name="flagit.update"),
]
