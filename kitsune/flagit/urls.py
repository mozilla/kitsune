from django.conf.urls import url

from kitsune.flagit import views

urlpatterns = [
    url(r"^$", views.queue, name="flagit.queue"),
    url(r"^/flag$", views.flag, name="flagit.flag"),
    url(r"^/update/(?P<flagged_object_id>\d+)$", views.update, name="flagit.update"),
]
