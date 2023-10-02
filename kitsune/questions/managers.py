from datetime import datetime, timedelta

from django.db.models import F, Manager, Q
from django.db.models.functions import Now

from kitsune.questions import config


class QuestionManager(Manager):
    # If question is marked as "locked" or "solved"
    #     the status is "Done"
    def done(self):
        return self.filter(Q(solution__isnull=False) | Q(is_locked=True))

    # else if contributor is last to post
    #     the status is "Responded"
    def responded(self):
        return self.filter(
            solution__isnull=True, is_locked=False, is_archived=False, last_answer__isnull=False
        ).exclude(last_answer__creator=F("creator"))

    # else if OP is last to post
    #      the status is "Needs Attention"
    def needs_attention(self):
        # Use "__range" to ensure the database index is used in Postgres.
        qs = self.filter(
            solution__isnull=True,
            is_locked=False,
            is_archived=False,
            updated__range=(datetime.now() - timedelta(days=7), Now()),
        )
        return qs.filter(Q(last_answer__creator=F("creator")) | Q(last_answer__isnull=True))

    def recently_unanswered(self):
        # Use "__range" to ensure the database index is used in Postgres.
        return self.filter(
            last_answer__isnull=True,
            is_locked=False,
            created__range=(datetime.now() - timedelta(hours=24), Now()),
        )

    def new(self):
        # Use "__range" to ensure the database index is used in Postgres.
        return self.filter(
            last_answer__isnull=True,
            is_locked=False,
            created__range=(datetime.now() - timedelta(days=7), Now()),
        )

    def unhelpful_answers(self):
        # Use "__range" to ensure the database index is used in Postgres.
        return self.filter(
            solution__isnull=True,
            is_locked=False,
            last_answer__creator=F("creator"),
            created__range=(datetime.now() - timedelta(days=7), Now()),
        )

    def needs_info(self):
        qs = self.filter(
            solution__isnull=True, is_locked=False, tags__slug__in=[config.NEEDS_INFO_TAG_NAME]
        )
        return qs.exclude(last_answer__creator=F("creator"))

    def solution_provided(self):
        qs = self.filter(solution__isnull=True, is_locked=False)
        return qs.exclude(last_answer__creator=F("creator"))

    def locked(self):
        return self.filter(is_locked=True)

    def solved(self):
        return self.filter(solution__isnull=False)


class QuestionLocaleManager(Manager):
    def locales_list(self):
        return self.values_list("locale", flat=True)


class AnswerManager(Manager):
    def not_by_asker(self):
        """Answers by anyone except the user who asked the question"""
        return self.exclude(creator=F("question__creator"))
