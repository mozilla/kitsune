from datetime import datetime, timedelta
from functools import lru_cache

from django.db.models import F, Manager, Q
from django.db.models.functions import Now

from kitsune.questions import config
from kitsune.users.models import Profile


@lru_cache(maxsize=1)
def get_sumo_bot():
    """Get the SuMo bot user with caching."""
    return Profile.get_sumo_bot()


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

    def locked(self):
        return self.filter(is_locked=True)

    def solved(self):
        return self.filter(solution__isnull=False)

    def spam(self):
        return self.filter(is_spam=True)

    def detected_spam(self):
        sumo_bot = get_sumo_bot()
        return self.filter(is_spam=True, marked_as_spam_by=sumo_bot)

    def undetected_spam(self):
        sumo_bot = get_sumo_bot()
        return self.filter(is_spam=True).exclude(marked_as_spam_by=sumo_bot)


class AAQConfigManager(Manager):
    def locales_list(self):
        return (
            self.filter(enabled_locales__locale__isnull=False)
            .values_list("enabled_locales__locale", flat=True)
            .distinct()
        )


class AnswerManager(Manager):
    def not_by_asker(self):
        """Answers by anyone except the user who asked the question"""
        return self.exclude(creator=F("question__creator"))
