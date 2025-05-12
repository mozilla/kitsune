from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from kitsune.flagit.models import FlaggedObject
from kitsune.products.models import Topic
from kitsune.questions.models import Question
from kitsune.users.models import Profile


def flag_as_spam(question: Question, reason: str) -> None:
    """
    Flags the given question as spam with the given reason.
    """
    if question.is_spam:
        return

    sumo_bot = Profile.get_sumo_bot()

    with transaction.atomic():
        # Mark the question as spam, and assign it the "Undefined" topic.
        question.topic = Topic.active.get(title="Undefined")
        question.mark_as_spam(by_user=sumo_bot)

        notes = f"Automatically flagged and marked as spam for the following reason:\n{reason}"

        # Flag it as spam, to allow review by moderators.
        flagged_object, created = FlaggedObject.objects.get_or_create(
            creator=sumo_bot,
            object_id=question.id,
            content_type=ContentType.objects.get_for_model(Question),
            defaults=dict(
                content_object=question,
                reason=FlaggedObject.REASON_SPAM,
                notes=notes,
            ),
        )
        if not created:
            flagged_object.reason = FlaggedObject.REASON_SPAM
            flagged_object.status = FlaggedObject.FLAG_PENDING
            flagged_object.notes = notes
            flagged_object.save()


def assign_topic(question: Question, topic_title: str, reason: str) -> None:
    """
    Assigns the topic identified by the given topic title to the question,
    and with the given reason.
    """
    try:
        topic = Topic.active.get(title=topic_title)
    except Topic.DoesNotExist:
        raise ValueError(f'No topic exists with the title "{topic_title}".')

    if question.topic:
        return

    question.topic = topic
    question.updated = datetime.now()
    question.updated_by = Profile.get_sumo_bot()
    question.save()
