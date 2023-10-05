from django.conf import settings
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import RedirectView
from django.views.static import serve as servestatic
from graphene_django.views import GraphQLView
from waffle.views import wafflejs

from kitsune.dashboards.api import WikiMetricList
from kitsune.sumo import views as sumo_views
from kitsune.sumo.i18n import i18n_patterns

# Note: This must come before importing admin because it patches the
# admin.
from kitsune.sumo.monkeypatch import patch

patch()

from django.contrib import admin  # noqa

admin.autodiscover()

urlpatterns = i18n_patterns(
    path("kb", include("kitsune.wiki.urls")),
    path("search/", include("kitsune.search.urls")),
    path("forums/", include("kitsune.forums.urls")),
    path("questions/", include("kitsune.questions.urls")),
    path("flagged/", include("kitsune.flagit.urls")),
    path("upload/", include("kitsune.upload.urls")),
    path("gallery/", include("kitsune.gallery.urls")),
    path("chat", RedirectView.as_view(url="questions/new")),
    path("messages/", include("kitsune.messages.urls")),
    path("groups/", include("kitsune.groups.urls")),
    path("kpi/", include("kitsune.kpi.urls")),
    path("products/", include("kitsune.products.urls")),
    path("announcements/", include("kitsune.announcements.urls")),
    path("community/", include("kitsune.community.urls")),
    path("badges/", include("kitsune.kbadge.urls")),
    path("", include("kitsune.dashboards.urls")),
    path("", include("kitsune.landings.urls")),
    path("", include("kitsune.tidings.urls")),
    path("", include("kitsune.users.urls")),
    path("locales", sumo_views.locales, name="sumo.locales"),
    re_path(r"^windows7-support(?:\\/)?$", RedirectView.as_view(url="/home/?as=u")),
)

if settings.OIDC_ENABLE:
    urlpatterns.append(path("", include("kitsune.users.urls_oidc")))

urlpatterns += [
    path("1/", include("kitsune.inproduct.urls")),
    path("postcrash", include("kitsune.postcrash.urls")),
    path("wafflejs", wafflejs, name="wafflejs"),
    path("", include("kitsune.kpi.urls_api")),
    path("", include("kitsune.sumo.urls")),
    # v1 APIs
    path("api/1/kb/", include("kitsune.wiki.urls_api")),
    path("api/1/products/", include("kitsune.products.urls_api")),
    path("api/1/gallery/", include("kitsune.gallery.urls_api")),
    path("api/1/users/", include("kitsune.users.urls_api")),
    # API to pull wiki metrics data.
    re_path(r"^api/v1/wikimetrics/?$", WikiMetricList.as_view(), name="api.wikimetric_list"),
    # v2 APIs
    path("api/2/", include("kitsune.notifications.urls_api")),
    path("api/2/", include("kitsune.questions.urls_api")),
    path("api/2/", include("kitsune.sumo.urls_api")),
    # These API urls include both v1 and v2 urls.
    path("api/", include("kitsune.users.urls_api")),
    # contribute.json
    re_path(
        r"^(?P<path>contribute\.json)$",
        servestatic,
        kwargs={"document_root": settings.ROOT},
    ),
    # GraphiQL
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
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
