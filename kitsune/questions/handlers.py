from dataclasses import dataclass, field

from django.conf import settings
from django.contrib.auth.models import User

from kitsune.questions.models import Answer, Question
from kitsune.sumo.handlers import AbstractChain, AccountHandler


class SpamAAQHandler(AccountHandler):
    """Handler for spam cleanup."""

    def handle_account(self, data: dict) -> None:
        """Handler to delete all spam questions and answers for a given user."""
        questions = data["questions"]
        answers = data["answers"]

        spam_questions = questions.filter(is_spam=True).values_list("id", flat=True)
        spam_answers = answers.filter(is_spam=True).values_list("id", flat=True)
        Question.objects.filter(id__in=spam_questions).delete()
        Answer.objects.filter(id__in=spam_answers).delete()


class ArchivedProductAAQHandler(AccountHandler):
    """Handler for archived product cleanup."""

    def handle_account(self, data: dict) -> None:
        """Handler to delete all forum posts for a given user for archived products."""
        questions = data["questions"]
        answers = data["answers"]

        archived_questions = questions.filter(product__is_archived=True).values_list(
            "id", flat=True
        )
        archived_answers = answers.filter(question__in=archived_questions).values_list(
            "id", flat=True
        )
        Question.objects.filter(id__in=archived_questions).delete()
        Answer.objects.filter(id__in=archived_answers).delete()


class OrphanedQuestionAAQHandler(AccountHandler):
    """Handler for orphaned question cleanup."""

    def handle_account(self, data: dict) -> None:
        """Handler to delete all questions without answers."""
        questions = data["questions"]

        orphaned_questions = questions.filter(num_answers=0).values_list("id", flat=True)
        Question.objects.filter(id__in=orphaned_questions).delete()


FORUM_HANDLERS = [
    SpamAAQHandler(),
    ArchivedProductAAQHandler(),
    OrphanedQuestionAAQHandler(),
]


@dataclass
class AAQChain(AbstractChain[AccountHandler]):
    """Chain of handlers for AAQ tasks."""

    _handlers: list[AccountHandler] = field(
        default_factory=lambda: list(FORUM_HANDLERS), init=False
    )

    def run(self, user: User) -> None:
        """Run the chain of handlers."""
        data = {
            "questions": Question.objects.filter(creator=user),
            "answers": Answer.objects.filter(creator=user),
        }

        for handler in self.handlers:
            handler.handle_account(data)

        # Re-assign remaining questions and answers to SumoBot.
        try:
            sumo_bot = User.objects.get(username=settings.SUMO_BOT_USERNAME)
        except User.DoesNotExist:
            raise ValueError("SumoBot user not found")
        else:
            Question.objects.filter(creator=user).update(creator=sumo_bot)
            Answer.objects.filter(creator=user).update(creator=sumo_bot)
