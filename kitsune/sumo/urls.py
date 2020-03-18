from django.conf.urls import url, include
from django.views.generic.base import RedirectView

from watchman import views as watchman_views

from kitsune.sumo import views


services_patterns = [
    url("^/monitor$", views.monitor, name="sumo.monitor"),
    url("^/version$", views.version_check, name="sumo.version"),
    url("^/error$", views.error, name="sumo.error"),
]


urlpatterns = [
    url(r"^robots.txt$", views.robots, name="robots.txt"),
    url(r"^services/", include(services_patterns)),
    url("^locales$", views.locales, name="sumo.locales"),
    url("^geoip-suggestion$", views.geoip_suggestion, name="sumo.geoip_suggestion"),
    url(r"^healthz/$", watchman_views.ping, name="sumo.liveness"),
    url(r"^readiness/$", watchman_views.status, name="sumo.readiness"),
    # Shortcuts:
    url("^contribute/?$", RedirectView.as_view(url="/get-involved", permanent=False)),
    url(
        r"^windows7-support(?:\\/)?$",
        RedirectView.as_view(url="/home/?as=u", permanent=False),
    ),
]
