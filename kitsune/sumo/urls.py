from django.urls import re_path
from django.views.generic.base import RedirectView
from watchman import views as watchman_views

from kitsune.sumo import views

urlpatterns = [
    re_path(r"^robots.txt$", views.robots, name="robots.txt"),
    re_path(r"^manifest.json$", views.manifest, name="manifest.json"),
    re_path("^locales$", views.locales, name="sumo.locales"),
    re_path("^geoip-suggestion$", views.geoip_suggestion, name="sumo.geoip_suggestion"),
    re_path(r"^healthz/$", watchman_views.ping, name="sumo.liveness"),
    re_path(r"^readiness/$", watchman_views.status, name="sumo.readiness"),
    # Shortcuts:
    re_path("^contribute/?$", RedirectView.as_view(url="/get-involved", permanent=False)),
    re_path(
        r"^windows7-support(?:\\/)?$", RedirectView.as_view(url="/home/?as=u", permanent=False)
    ),
]
