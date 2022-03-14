from django.urls import re_path

from kitsune.dashboards import api, views

urlpatterns = [
    re_path(r"^localization$", views.localization, name="dashboards.localization"),
    re_path(r"^contributors$", views.contributors, name="dashboards.contributors"),
    re_path(r"^contributors-old$", views.contributors_old, name="dashboards.contributors_old"),
    re_path(
        r"^contributors/overview-rows$",
        views.contributors_overview_rows,
        name="dashboards.contributors_overview_rows",
    ),
    re_path(r"^wiki-rows/(?P<readout_slug>[^/]+)", views.wiki_rows, name="dashboards.wiki_rows"),
    re_path(
        r"^localization/(?P<readout_slug>[^/]+)",
        views.localization_detail,
        name="dashboards.localization_detail",
    ),
    re_path(
        r"^contributors/kb-overview$",
        views.contributors_overview,
        name="dashboards.contributors_overview",
    ),
    re_path(
        r"^contributors/(?P<readout_slug>[^/]+)",
        views.contributors_detail,
        name="dashboards.contributors_detail",
    ),
    # The aggregated kb metrics dashboard.
    re_path(
        r"^kb/dashboard/metrics/aggregated$",
        views.aggregated_metrics,
        name="dashboards.aggregated_metrics",
    ),
    # The per-locale kb metrics dashboard.
    re_path(
        r"^kb/dashboard/metrics/(?P<locale_code>[^/]+)$",
        views.locale_metrics,
        name="dashboards.locale_metrics",
    ),
    # API to pull wiki metrics data.
    re_path(r"^api/v1/wikimetrics/?$", api.WikiMetricList.as_view(), name="api.wikimetric_list"),
]
