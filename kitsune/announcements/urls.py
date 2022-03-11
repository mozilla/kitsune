from django.urls import re_path

from kitsune.announcements import views


urlpatterns = [
    re_path(r"^/create/locale$", views.create_for_locale, name="announcements.create_for_locale"),
    re_path(r"^/(?P<announcement_id>\d+)/delete$", views.delete, name="announcements.delete"),
]
