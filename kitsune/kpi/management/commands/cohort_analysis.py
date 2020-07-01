from datetime import datetime
from datetime import timedelta

from django.core.management.base import BaseCommand

from kitsune.customercare.models import Reply
from kitsune.kpi.management import utils
from kitsune.kpi.models import AOA_CONTRIBUTOR_COHORT_CODE
from kitsune.kpi.models import Cohort
from kitsune.kpi.models import CohortKind
from kitsune.kpi.models import CONTRIBUTOR_COHORT_CODE
from kitsune.kpi.models import KB_ENUS_CONTRIBUTOR_COHORT_CODE
from kitsune.kpi.models import KB_L10N_CONTRIBUTOR_COHORT_CODE
from kitsune.kpi.models import RetentionMetric
from kitsune.kpi.models import SUPPORT_FORUM_HELPER_COHORT_CODE
from kitsune.questions.models import Answer
from kitsune.wiki.models import Revision


class Command(BaseCommand):
    def handle(self, **options):
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        boundaries = [today - timedelta(days=today.weekday())]
        for _ in range(12):
            previous_week = boundaries[-1] - timedelta(weeks=1)
            boundaries.append(previous_week)
        boundaries.reverse()
        ranges = list(zip(boundaries[:-1], boundaries[1:]))

        reports = [
            (
                CONTRIBUTOR_COHORT_CODE,
                [
                    (Revision.objects.all(), ("creator", "reviewer")),
                    (Answer.objects.not_by_asker(), ("creator",)),
                    (Reply.objects.all(), ("user",)),
                ],
            ),
            (
                KB_ENUS_CONTRIBUTOR_COHORT_CODE,
                [(Revision.objects.filter(document__locale="en-US"), ("creator", "reviewer"),)],
            ),
            (
                KB_L10N_CONTRIBUTOR_COHORT_CODE,
                [(Revision.objects.exclude(document__locale="en-US"), ("creator", "reviewer"),)],
            ),
            (SUPPORT_FORUM_HELPER_COHORT_CODE, [(Answer.objects.not_by_asker(), ("creator",))],),
            (AOA_CONTRIBUTOR_COHORT_CODE, [(Reply.objects.all(), ("user",))]),
        ]

        for kind, querysets in reports:
            cohort_kind, _ = CohortKind.objects.get_or_create(code=kind)

            for i, cohort_range in enumerate(ranges):
                cohort_users = utils._get_cohort(querysets, cohort_range)

                # Sometimes None will be added to the cohort_users list, so remove it
                if None in cohort_users:
                    cohort_users.remove(None)

                cohort, _ = Cohort.objects.update_or_create(
                    kind=cohort_kind,
                    start=cohort_range[0],
                    end=cohort_range[1],
                    defaults={"size": len(cohort_users)},
                )

                for retention_range in ranges[i:]:
                    retained_user_count = utils._count_contributors_in_range(
                        querysets, cohort_users, retention_range
                    )
                    RetentionMetric.objects.update_or_create(
                        cohort=cohort,
                        start=retention_range[0],
                        end=retention_range[1],
                        defaults={"size": retained_user_count},
                    )
