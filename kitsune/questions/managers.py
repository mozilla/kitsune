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
        return self.filter(solution__isnull=True, is_locked=False).filter(
            Q(last_answer__creator=F('creator')) | Q(last_answer__isnull=True))

    def needs_info(self):
        return self.filter(tags__slug__in=[config.NEEDS_INFO_TAG_NAME])

    def escalated(self):
        return self.filter(tags__slug__in=[config.ESCALATE_TAG_NAME])
