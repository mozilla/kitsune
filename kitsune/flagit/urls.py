from django.urls import path

from kitsune.flagit import views

urlpatterns = [
    path("", views.queue, name="flagit.queue"),
    path("flag", views.flag, name="flagit.flag"),
    path("update/<int:flagged_object_id>", views.update, name="flagit.update"),
]
