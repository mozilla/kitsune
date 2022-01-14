from django.urls import include, re_path
from rest_framework import routers

from kitsune.kpi import api
from kitsune.kpi.models import (
    CONTRIBUTORS_CSAT_METRIC_CODE,
    KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE,
    KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE,
    SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE,
)

router = routers.SimpleRouter()
router.register(r"cohort", api.CohortViewSet)

urlpatterns = [
    re_path(
        r"^api/v1/kpi/csat-contributors/?$",
        api.CSATMetricList.as_view(code=CONTRIBUTORS_CSAT_METRIC_CODE),
        name="api.kpi.csat-contributors",
    ),
    re_path(
        r"^api/v1/kpi/csat-contributors/support-forum/?$",
        api.CSATMetricList.as_view(code=SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE),
        name="api.kpi.csat-contributors-support-forum",
    ),
    re_path(
        r"^api/v1/kpi/csat-contributors/kb-enus/?$",
        api.CSATMetricList.as_view(code=KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE),
        name="api.kpi.csat-contributors-kb-enus",
    ),
    re_path(
        r"^api/v1/kpi/csat-contributors/kb-l10n/?$",
        api.CSATMetricList.as_view(code=KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE),
        name="api.kpi.csat-contributors-kb-l10n",
    ),
    re_path(
        r"^api/v1/kpi/l10n-coverage/?$",
        api.L10nCoverageMetricList.as_view(),
        name="api.kpi.l10n-coverage",
    ),
    re_path(
        r"^api/v1/kpi/exit-survey/?$",
        api.ExitSurveyMetricList.as_view(),
        name="api.kpi.exit-survey",
    ),
    re_path(r"^api/v1/kpi/visitors/?$", api.VisitorsMetricList.as_view(), name="api.kpi.visitors"),
    re_path(
        r"^api/v1/kpi/contributors/?$",
        api.ContributorsMetricList.as_view(),
        name="api.kpi.contributors",
    ),
    re_path(r"^api/v1/kpi/kb-votes/?$", api.KBVoteMetricList.as_view(), name="api.kpi.kb-votes"),
    re_path(r"^api/v1/kpi/votes/?$", api.VoteMetricList.as_view(), name="api.kpi.votes"),
    re_path(
        r"^api/v1/kpi/questions/?$", api.QuestionsMetricList.as_view(), name="api.kpi.questions"
    ),
    re_path(
        r"^api/v1/kpi/search-ctr/?$",
        api.SearchClickthroughMetricList.as_view(),
        name="api.kpi.search-ctr",
    ),
    re_path(r"^api/2/", include(router.urls)),
]
