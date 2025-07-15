import waffle
from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from kitsune.flagit.models import FlaggedObject
from kitsune.llm.questions.classifiers import classify_question
from kitsune.users.models import Profile

shared_task_with_retry = shared_task(
    acks_late=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)


@shared_task_with_retry
def question_classifier(question_id):
    from kitsune.questions.models import Question
    from kitsune.questions.utils import flag_question, process_classification_result

    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return

    if waffle.switch_is_active("auto-question-classifier"):
        result = classify_question(question)
        process_classification_result(question, result)
    elif waffle.switch_is_active("flagit-spam-autoflag"):
        flag_question(
            question,
            reason=FlaggedObject.REASON_CONTENT_MODERATION,
            status=FlaggedObject.FLAG_PENDING,
            by_user=Profile.get_sumo_bot(),
            notes=(
                "Automatically flagged for topic moderation: auto-question-classifier is disabled"
            ),
        )


@shared_task_with_retry
def process_moderation_queue(batch_size=10):
    """
    Process flagged objects in the moderation queue through the LLM pipeline.

    Args:
        batch_size: Number of items to process in this batch
    """
    from kitsune.questions.models import Question
    from kitsune.questions.utils import process_classification_result

    if not waffle.switch_is_active("auto-question-classifier"):
        return

    stale_flags = FlaggedObject.objects.filter(
        status=FlaggedObject.FLAG_PENDING,
        reason=FlaggedObject.REASON_CONTENT_MODERATION,
        content_type=ContentType.objects.get_for_model(Question),
    ).select_related("creator")[:batch_size]

    processed_count = 0
    for flagged_obj in stale_flags:
        status = FlaggedObject.FLAG_REJECTED
        if question := flagged_obj.content_object:
            try:
                result = classify_question(question)
            except Exception as e:
                flag_note = f"Error processing through LLM: {e!s}"
            else:
                status = FlaggedObject.FLAG_ACCEPTED

                action = result.get("action")

                notes_parts = [
                    "Processed by LLM stale queue processor",
                    f"Action: {action}",
                ]

                for key, value in result.items():
                    if isinstance(value, dict) and "reason" in value and value["reason"]:
                        notes_parts.append(
                            f"{key.replace('_', ' ').title()} reason: {value['reason']}"
                        )

                flag_note = "\n".join(notes_parts)
                process_classification_result(question, result)
                processed_count += 1
        else:
            flag_note = "Content object no longer exists"

        flagged_obj.status = status
        flagged_obj.notes = flag_note
        flagged_obj.handled_by = Profile.get_sumo_bot()
        flagged_obj.handled = timezone.now()
        flagged_obj.save()

    return f"Processed {processed_count} stale flagged objects"
