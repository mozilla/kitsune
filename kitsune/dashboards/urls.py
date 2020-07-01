from django.conf.urls import url

from kitsune.dashboards import api
from kitsune.dashboards import views


urlpatterns = [
    url(r"^localization$", views.localization, name="dashboards.localization"),
    url(r"^contributors$", views.contributors, name="dashboards.contributors"),
    url(r"^contributors-old$", views.contributors_old, name="dashboards.contributors_old"),
    url(
        r"^contributors/overview-rows$",
        views.contributors_overview_rows,
        name="dashboards.contributors_overview_rows",
    ),
    url(r"^wiki-rows/(?P<readout_slug>[^/]+)", views.wiki_rows, name="dashboards.wiki_rows"),
    url(
        r"^localization/(?P<readout_slug>[^/]+)",
        views.localization_detail,
        name="dashboards.localization_detail",
    ),
    url(
        r"^contributors/kb-overview$",
        views.contributors_overview,
        name="dashboards.contributors_overview",
    ),
    url(
        r"^contributors/(?P<readout_slug>[^/]+)",
        views.contributors_detail,
        name="dashboards.contributors_detail",
    ),
    # The aggregated kb metrics dashboard.
    url(
        r"^kb/dashboard/metrics/aggregated$",
        views.aggregated_metrics,
        name="dashboards.aggregated_metrics",
    ),
    # The per-locale kb metrics dashboard.
    url(
        r"^kb/dashboard/metrics/(?P<locale_code>[^/]+)$",
        views.locale_metrics,
        name="dashboards.locale_metrics",
    ),
    # API to pull wiki metrics data.
    url(r"^api/v1/wikimetrics/?$", api.WikiMetricList.as_view(), name="api.wikimetric_list"),
]
