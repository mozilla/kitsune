from django.conf import settings
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import RedirectView
from django.views.static import serve as servestatic
from graphene_django.views import GraphQLView
from waffle.views import wafflejs
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from kitsune.sumo import views as sumo_views

# Note: This must come before importing admin because it patches the
# admin.
from kitsune.sumo.monkeypatch import patch

patch()

from django.contrib import admin  # noqa

admin.autodiscover()

urlpatterns = [
    re_path(r"^search/", include("kitsune.search.urls")),
    re_path(r"forums/", include("kitsune.forums.urls")),
    re_path(r"^questions/", include("kitsune.questions.urls")),
    re_path(r"^flagged/", include("kitsune.flagit.urls")),
    re_path(r"^upload/", include("kitsune.upload.urls")),
    re_path(r"^kb", include("kitsune.wiki.urls")),
    re_path(r"^gallery/", include("kitsune.gallery.urls")),
    re_path(r"^chat", RedirectView.as_view(url="questions/new")),
    re_path(r"^messages/", include("kitsune.messages.urls")),
    re_path(r"^1/", include("kitsune.inproduct.urls")),
    re_path(r"^postcrash", include("kitsune.postcrash.urls")),
    re_path(r"^groups/", include("kitsune.groups.urls")),
    re_path(r"^kpi/", include("kitsune.kpi.urls")),
    re_path(r"^products/", include("kitsune.products.urls")),
    re_path(r"^announcements/", include("kitsune.announcements.urls")),
    re_path(r"^community/", include("kitsune.community.urls")),
    re_path(r"^badges/", include("kitsune.kbadge.urls")),
    # JavaScript Waffle.
    re_path(r"^wafflejs$", wafflejs, name="wafflejs"),
    re_path(r"^", include("kitsune.dashboards.urls")),
    re_path(r"^", include("kitsune.landings.urls")),
    re_path(r"^", include("kitsune.kpi.urls_api")),
    re_path(r"^", include("kitsune.tidings.urls")),
    # Users
    re_path("", include("kitsune.users.urls")),
    # Services and sundry.
    re_path(r"", include("kitsune.sumo.urls")),
    # v1 APIs
    re_path(r"^api/1/kb/", include("kitsune.wiki.urls_api")),
    re_path(r"^api/1/products/", include("kitsune.products.urls_api")),
    re_path(r"^api/1/gallery/", include("kitsune.gallery.urls_api")),
    re_path(r"^api/1/users/", include("kitsune.users.urls_api")),
    # v2 APIs
    re_path(r"^api/2/", include("kitsune.notifications.urls_api")),
    re_path(r"^api/2/", include("kitsune.questions.urls_api")),
    re_path(r"^api/2/", include("kitsune.sumo.urls_api")),
    # These API urls include both v1 and v2 urls.
    re_path(r"^api/", include("kitsune.users.urls_api")),
    # contribute.json url
    re_path(
        r"^(?P<path>contribute\.json)$",
        servestatic,
        kwargs={"document_root": settings.ROOT},
    ),
    # GraphiQL
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    # Wagtail
    path("cms/", include(wagtailadmin_urls)),
    path("wagtail-docs/", include(wagtaildocs_urls)),
    path("wagtail-kb/", include(wagtail_urls)),
]

# Handle 404 and 500 errors
handler404 = sumo_views.handle404
handler500 = sumo_views.handle500

if settings.DEBUG:
    media_url = settings.MEDIA_URL.lstrip("/").rstrip("/")
    urlpatterns += [
        re_path(
            r"^%s/(?P<path>.*)$" % media_url,
            sumo_views.serve_cors,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]

if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns += [
        re_path("__debug__/", include(debug_toolbar.urls)),
    ]


if settings.ENABLE_ADMIN:
    urlpatterns += [
        re_path(r"^admin/", admin.site.urls),
    ]
elif settings.ADMIN_REDIRECT_URL:
    urlpatterns.append(re_path(r"^admin/", RedirectView.as_view(url=settings.ADMIN_REDIRECT_URL)))
