from django.conf.urls import url

from kitsune.announcements import views


urlpatterns = [
    url(
        r"^/create/locale$",
        views.create_for_locale,
        name="announcements.create_for_locale",
    ),
    url(
        r"^/(?P<announcement_id>\d+)/delete$", views.delete, name="announcements.delete"
    ),
]
