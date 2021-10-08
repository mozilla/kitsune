import authority
from django.conf import settings
from django.conf.urls import include, url
from django.urls import path
from django.views.generic.base import RedirectView
from django.views.static import serve as servestatic
from waffle.views import wafflejs

from kitsune.sumo import views as sumo_views

# Note: This must come before importing admin because it patches the
# admin.
from kitsune.sumo.monkeypatch import patch

patch()

from django.contrib import admin  # noqa

admin.autodiscover()

authority.autodiscover()

urlpatterns = [
    path("search/", include("kitsune.search.urls")),
    path("forums/", include("kitsune.forums.urls")),
    path("questions/", include("kitsune.questions.urls")),
    path("flagged/", include("kitsune.flagit.urls")),
    path("upload/", include("kitsune.upload.urls")),
    url(r"^kb", include("kitsune.wiki.urls")),
    url(r"^gallery", include("kitsune.gallery.urls")),
    url(r"^chat", RedirectView.as_view(url="questions/new")),
    url(r"^messages", include("kitsune.messages.urls")),
    url(r"^1", include("kitsune.inproduct.urls")),
    url(r"^postcrash", include("kitsune.postcrash.urls")),
    url(r"^groups", include("kitsune.groups.urls")),
    url(r"^kpi/", include("kitsune.kpi.urls")),
    url(r"^products", include("kitsune.products.urls")),
    url(r"^announcements", include("kitsune.announcements.urls")),
    url(r"^community", include("kitsune.community.urls")),
    url(r"^badges/", include("kitsune.kbadge.urls")),
    # JavaScript Waffle.
    url(r"^wafflejs$", wafflejs, name="wafflejs"),
    url(r"^", include("kitsune.dashboards.urls")),
    url(r"^", include("kitsune.landings.urls")),
    url(r"^", include("kitsune.kpi.urls_api")),
    url(r"^", include("kitsune.motidings.urls")),
    # Users
    url("", include("kitsune.users.urls")),
    # Services and sundry.
    url(r"", include("kitsune.sumo.urls")),
    # v1 APIs
    url(r"^api/1/kb/", include("kitsune.wiki.urls_api")),
    url(r"^api/1/products/", include("kitsune.products.urls_api")),
    url(r"^api/1/gallery/", include("kitsune.gallery.urls_api")),
    url(r"^api/1/users/", include("kitsune.users.urls_api")),
    # v2 APIs
    url(r"^api/2/", include("kitsune.notifications.urls_api")),
    url(r"^api/2/", include("kitsune.questions.urls_api")),
    url(r"^api/2/", include("kitsune.sumo.urls_api")),
    # These API urls include both v1 and v2 urls.
    url(r"^api/", include("kitsune.users.urls_api")),
    # contribute.json url
    url(
        r"^(?P<path>contribute\.json)$",
        servestatic,
        kwargs={"document_root": settings.ROOT},
    ),
]

# Handle 404 and 500 errors
handler404 = sumo_views.handle404
handler500 = sumo_views.handle500

if settings.DEBUG:
    media_url = settings.MEDIA_URL.lstrip("/").rstrip("/")
    urlpatterns += [
        url(
            r"^%s/(?P<path>.*)$" % media_url,
            sumo_views.serve_cors,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]

if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns += [
        url("__debug__/", include(debug_toolbar.urls)),
    ]


if settings.ENABLE_ADMIN:
    urlpatterns += [
        url(r"^admin/", admin.site.urls),
    ]
elif settings.ADMIN_REDIRECT_URL:
    urlpatterns.append(url(r"^admin/", RedirectView.as_view(url=settings.ADMIN_REDIRECT_URL)))
