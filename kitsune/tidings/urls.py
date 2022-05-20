from django.urls import re_path

from kitsune.tidings import views

urlpatterns = [
    re_path(r"^unsubscribe/(?P<watch_id>\d+)$", views.unsubscribe, name="tidings.unsubscribe")
]
