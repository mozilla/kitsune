from django.urls import re_path

from kitsune.motidings import views

# Note: This overrides the tidings tidings.unsubscribe url pattern, so
# we need to keep the name exactly as it is.
urlpatterns = [
    re_path(r"^unsubscribe/(?P<watch_id>\d+)$", views.unsubscribe, name="tidings.unsubscribe")
]
