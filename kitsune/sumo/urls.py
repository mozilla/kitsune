from django.urls import path
from watchman import views as watchman_views

from kitsune.sumo import views


urlpatterns = [
    path("robots.txt", views.robots, name="robots.txt"),
    path("healthz/", watchman_views.ping, name="sumo.liveness"),
    path("readiness/", watchman_views.status, name="sumo.readiness"),
    path("manifest.json", views.manifest, name="manifest.json"),
    path("geoip-suggestion", views.geoip_suggestion, name="sumo.geoip_suggestion"),
]
