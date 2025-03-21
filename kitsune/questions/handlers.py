from dataclasses import dataclass, field

from django.contrib.auth.models import User
from django.utils.translation import gettext as _

from kitsune.questions.models import Answer, AnswerVote, Question, QuestionVote
from kitsune.sumo.anonymous import AnonymousIdentity
from kitsune.sumo.handlers import AbstractChain, AccountHandler
from kitsune.users.handlers import UserDeletionListener
from kitsune.users.models import Profile


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

        sumo_bot = Profile.get_sumo_bot()

        questions_to_update = list(Question.objects.filter(creator=user))

        Question.objects.filter(creator=user).update(creator=sumo_bot, is_locked=True)
        Answer.objects.bulk_create(
            [
                Answer(
                    creator=sumo_bot,
                    content=_(
                        "This question has been locked because the original author has "
                        "deleted their account. While you can no longer post new replies, "
                        "the existing content remains available for reference."
                    ),
                    question=question,
                )
                for question in questions_to_update
            ]
        )

        Answer.objects.filter(creator=user).update(creator=sumo_bot)

        anonymous_id = AnonymousIdentity().anonymous_id
        QuestionVote.objects.filter(creator=user).update(creator=None, anonymous_id=anonymous_id)
        AnswerVote.objects.filter(creator=user).update(creator=None, anonymous_id=anonymous_id)


class AAQListener(UserDeletionListener):
    """Listener for AAQ-related tasks."""

    def on_user_deletion(self, user: User) -> None:
        """Handle the deletion of a user."""
        AAQChain().run(user)
