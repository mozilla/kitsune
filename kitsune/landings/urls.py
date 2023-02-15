from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from wagtail import urls as wagtail_urls

from kitsune.landings import views
from kitsune.sumo.views import redirect_to

urlpatterns = [
    re_path(r"^$", views.home, name="home"),
    # Redirect from old home re_path /home to new home /
    re_path(r"^home$", redirect_to, {"url": "home"}, name="old_home"),
    path("wg/", include(wagtail_urls)),
    re_path(r"^topics/hot$", redirect_to, {"url": "products"}, name="hot_topics"),
    # Redirect from old mobile URL to new one.
    re_path(
        r"^mobile$",
        redirect_to,
        {"url": "products.product", "slug": "mobile"},
        name="home.mobile",
    ),
    # A static page for downloading FirefoxIntegrityCheck.exe
    re_path(
        r"^download-firefox-integrity-check$",
        views.integrity_check,
        name="download.integrity-check",
    ),
    re_path(r"^contribute/?.*$", views.contribute, name="landings.contribute"),
    re_path(
        r"^get-involved/?.*$",
        RedirectView.as_view(pattern_name="landings.contribute", permanent=True),
    ),
]
