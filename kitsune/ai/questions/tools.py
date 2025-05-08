from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from langchain_core.tools import tool

from kitsune.ai.utils import close_db_connection_when_done
from kitsune.flagit.models import FlaggedObject
from kitsune.products.models import Topic
from kitsune.questions.models import Question
from kitsune.users.models import Profile


@tool
def flag_as_spam(question_id: int, reason: str) -> str:
    """
    Flags the given question as spam with the given reason.

    Args:
        question_id (int): The ID of the question to flag as spam.
        reason (str): The reason for flagging the question as spam.

    Returns:
        message (str): A message that describes what was done.
    """
    return do_flag_as_spam(question_id, reason)


@tool
def assign_topic(question_id: int, topic_title: str, reason: str) -> str:
    """
    Assigns the topic identified by the given topic title to the question
    identified by the given question ID, and with the given reason.

    Args:
        question_id (int): The ID of the question to which the topic will be assigned.
        topic_title (str): The title of the topic that will be assigned to the question.
        reason (str): The reason for assigning the topic to the question.

    Returns:
        message (str): A message that describes what was done.
    """
    return do_assign_topic(question_id, topic_title, reason)


@close_db_connection_when_done
def do_flag_as_spam(question_id: int, reason: str) -> str:
    """
    Flags the given question as spam with the given reason.
    """
    flagged_phrase = f"flagged and marked as spam for the following reason:\n{reason}"

    print("Tool call: flag_as_spam():")
    print(f"    question.id = {question_id}")
    print(f"    reason:\n{reason}")

    try:
        question = Question.objects.select_related("topic").get(id=question_id)
    except Question.DoesNotExist:
        return (
            f"Question {question_id} does not exist. If it had existed, it would have"
            f" been {flagged_phrase}"
        )

    if question.is_spam:
        return (
            f"Question {question_id} was already marked as spam. If it had not been,"
            f" it would have been {flagged_phrase}"
        )

    sumo_bot = Profile.get_sumo_bot()

    with transaction.atomic():
        # Mark the question as spam, and assign it the "Undefined" topic.
        question.topic = Topic.active.get(title="Undefined")
        question.mark_as_spam(by_user=sumo_bot)

        notes = f"Automatically {flagged_phrase}"

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

    return f"Question {question_id} was {flagged_phrase}"


@close_db_connection_when_done
def do_assign_topic(question_id: int, topic_title: str, reason: str) -> str:
    """
    Assigns the topic identified by the given topic title to the question
    identified by the given question ID, and with the given reason.
    """
    print("Tool call: assign_topic():")
    print(f"    question.id = {question_id}")
    print(f"    topic.title = {topic_title}")
    print(f"    reason:\n{reason}")

    try:
        topic = Topic.active.get(title=topic_title)
    except Topic.DoesNotExist:
        raise ValueError(
            f'The "assign_topic" tool was given the invalid topic title "{topic_title}".'
        )

    assigned_phrase = f'assigned to the topic "{topic_title}" for the following reason:\n{reason}'

    try:
        question = Question.objects.select_related("topic").get(id=question_id)
    except Question.DoesNotExist:
        return (
            f"Question {question_id} does not exist. If it had existed, it would have"
            f" been {assigned_phrase}"
        )

    if question.topic:
        return (
            f"Question {question_id} had already been assigned a topic. If it hadn't, it"
            f" would have been {assigned_phrase}"
        )

    question.topic = topic
    question.updated = datetime.now()
    question.updated_by = Profile.get_sumo_bot()
    question.save()

    return f"Question {question_id} was {assigned_phrase}"
