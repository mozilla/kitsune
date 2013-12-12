from datetime import datetime, timedelta

from django.db.models import Q, F

from kitsune.questions import config
from kitsune.sumo.models import ManagerBase


class QuestionManager(ManagerBase):

    # If question is marked as "locked" or "solved"
    #     the status is "Done"
    def done(self):
        return self.filter(Q(solution__isnull=False) | Q(is_locked=True))

    # else if contributor is last to post
    #     the status is "Responded"
    def responded(self):
        return self.filter(
            solution__isnull=True,
            is_locked=False,
            last_answer__isnull=False).exclude(
                last_answer__creator=F('creator'))

    # else if OP is last to post
    #      the status is "Needs Attention"
    def needs_attention(self):
        qs = self.filter(solution__isnull=True, is_locked=False,
                         created__gte=datetime.now() - timedelta(days=7))
        return qs.filter(Q(last_answer__creator=F('creator')) |
                         Q(last_answer__isnull=True))

    def recently_unanswered(self):
        return self.filter(last_answer__isnull=True, is_locked=False,
                           created__gte=datetime.now() - timedelta(hours=24))

    def new(self):
        return self.filter(last_answer__isnull=True, is_locked=False,
                           created__gte=datetime.now() - timedelta(days=7))

    def unhelpful_answers(self):
        return self.filter(solution__isnull=True, is_locked=False,
                           last_answer__creator=F('creator'),
                           created__gte=datetime.now() - timedelta(days=7))

    def needs_info(self):
        qs = self.filter(solution__isnull=True, is_locked=False,
                         tags__slug__in=[config.NEEDS_INFO_TAG_NAME])
        return qs.exclude(last_answer__creator=F('creator'))

    def solution_provided(self):
        qs = self.filter(solution__isnull=True, is_locked=False)
        return qs.exclude(last_answer__creator=F('creator'))

    def locked(self):
        return self.filter(is_locked=True)

    def solved(self):
        return self.filter(solution__isnull=False)

    def escalated(self):
        return self.filter(tags__slug__in=[config.ESCALATE_TAG_NAME])
