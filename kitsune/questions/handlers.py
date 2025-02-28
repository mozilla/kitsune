from dataclasses import dataclass, field

from django.conf import settings
from django.contrib.auth.models import User

from kitsune.questions.models import Answer, Question
from kitsune.sumo.handlers import AbstractChain, AccountHandler
from kitsune.users.handlers import UserDeletionListener


class SpamAAQHandler(AccountHandler):
    """Handler for spam cleanup."""

    def handle_account(self, data: dict) -> None:
        """Handler to delete all spam questions and answers for a given user."""
        questions = data["questions"]
        answers = data["answers"]

        questions.filter(is_spam=True).delete()
        answers.filter(is_spam=True).delete()


class ArchivedProductAAQHandler(AccountHandler):
    """Handler for archived product cleanup."""

    def handle_account(self, data: dict) -> None:
        """Handler to delete all forum posts for a given user for archived products."""
        questions = data["questions"]
        questions.filter(product__is_archived=True).delete()


class OrphanedQuestionAAQHandler(AccountHandler):
    """Handler for orphaned question cleanup."""

    def handle_account(self, data: dict) -> None:
        """Handler to delete all questions without answers."""
        questions = data["questions"]

        questions.filter(num_answers=0).delete()


class ResetTakenByHandler(AccountHandler):
    """Handler to reset the taken_until field for a given user."""

    def handle_account(self, data: dict) -> None:
        """Handler to reset the taken_until field for a given user."""
        # taken_by will be updated to None when the user is deleted because of the cascade
        # set_null on the User model.
        questions = data["questions"]
        questions.filter(taken_by=data["user"]).update(taken_until=None)


FORUM_HANDLERS = [
    SpamAAQHandler(),
    ArchivedProductAAQHandler(),
    OrphanedQuestionAAQHandler(),
    ResetTakenByHandler(),
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
            "user": user,
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


class AAQListener(UserDeletionListener):
    """Listener for AAQ-related tasks."""

    def on_user_deletion(self, user: User) -> None:
        """Handle the deletion of a user."""
        AAQChain().run(user)
