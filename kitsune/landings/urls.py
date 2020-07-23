from django.conf.urls import url

from kitsune.landings import views
from kitsune.sumo.views import redirect_to


urlpatterns = [
    url(r"^$", views.home, name="home"),
    # Redirect from old home url /home to new home /
    url(r"^home$", redirect_to, {"url": "home"}, name="old_home"),
    url(r"^topics/hot$", redirect_to, {"url": "products"}, name="hot_topics"),
    # Redirect from old mobile URL to new one.
    url(
        r"^mobile$", redirect_to, {"url": "products.product", "slug": "mobile"}, name="home.mobile"
    ),
    # A static page for downloading FirefoxIntegrityCheck.exe
    url(
        r"^download-firefox-integrity-check$",
        views.integrity_check,
        name="download.integrity-check",
    ),
    url(
        r"^get-involved/questions$",
        views.get_involved_questions,
        name="landings.get_involved_questions",
    ),
    url(r"^get-involved/kb$", views.get_involved_kb, name="landings.get_involved_kb"),
    url(r"^get-involved/l10n$", views.get_involved_l10n, name="landings.get_involved_l10n"),
    url(r"^get-involved$", views.get_involved, name="landings.get_involved"),
]
