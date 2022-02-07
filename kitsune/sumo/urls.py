from django.conf.urls import url
from django.views.generic.base import RedirectView

from watchman import views as watchman_views

from kitsune.sumo import views


urlpatterns = [
    url(r"^robots.txt$", views.robots, name="robots.txt"),
    url(r"^manifest.json$", views.manifest, name="manifest.json"),
    url("^locales$", views.locales, name="sumo.locales"),
    url("^geoip-suggestion$", views.geoip_suggestion, name="sumo.geoip_suggestion"),
    url(r"^healthz/$", watchman_views.ping, name="sumo.liveness"),
    url(r"^readiness/$", watchman_views.status, name="sumo.readiness"),
    # Shortcuts:
    url(r"^windows7-support(?:\\/)?$", RedirectView.as_view(url="/home/?as=u", permanent=False)),
]
