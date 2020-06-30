from django.conf.urls import url

from kitsune.motidings import views


# Note: This overrides the tidings tidings.unsubscribe url pattern, so
# we need to keep the name exactly as it is.
urlpatterns = [
    url(r"^unsubscribe/(?P<watch_id>\d+)$", views.unsubscribe, name="tidings.unsubscribe")
]
