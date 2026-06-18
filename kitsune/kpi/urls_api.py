from django.urls import include, re_path
from rest_framework import routers

from kitsune.kpi import api

router = routers.SimpleRouter()
router.register(r"cohort", api.CohortViewSet)

urlpatterns = [
    re_path(
        r"^api/v1/kpi/l10n-coverage/?$",
        api.L10nCoverageMetricList.as_view(),
        name="api.kpi.l10n-coverage",
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
