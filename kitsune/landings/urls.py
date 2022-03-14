from django.urls import re_path

from kitsune.landings import views
from kitsune.sumo.views import redirect_to

urlpatterns = [
    re_path(r"^$", views.home, name="home"),
    # Redirect from old home re_path /home to new home /
    re_path(r"^home$", redirect_to, {"re_path": "home"}, name="old_home"),
    re_path(r"^topics/hot$", redirect_to, {"re_path": "products"}, name="hot_topics"),
    # Redirect from old mobile URL to new one.
    re_path(
        r"^mobile$",
        redirect_to,
        {"re_path": "products.product", "slug": "mobile"},
        name="home.mobile",
    ),
    # A static page for downloading FirefoxIntegrityCheck.exe
    re_path(
        r"^download-firefox-integrity-check$",
        views.integrity_check,
        name="download.integrity-check",
    ),
    re_path(
        r"^get-involved/questions$",
        views.get_involved_questions,
        name="landings.get_involved_questions",
    ),
    re_path(r"^get-involved/kb$", views.get_involved_kb, name="landings.get_involved_kb"),
    re_path(r"^get-involved/l10n$", views.get_involved_l10n, name="landings.get_involved_l10n"),
    re_path(r"^get-involved$", views.get_involved, name="landings.get_involved"),
    re_path(r"^contribute/?.*$", views.contribute, name="landings.contribute"),
]
