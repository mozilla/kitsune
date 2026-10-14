import json
import logging
from hashlib import sha256

import waffle
from celery import shared_task
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from kombu.exceptions import OperationalError

from kitsune.flagit.models import FlaggedObject
from kitsune.llm.spam.classifier import assess_spam
from kitsune.llm.support.classifiers import classify_question, question_payload, ticket_payload
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.users.models import Profile

log = logging.getLogger("k.task")

shared_task_with_retry = shared_task(
    acks_late=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)


def _assessment_digest(payload: dict[str, str]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def queue_spam_assessment(flag: FlaggedObject, result: dict) -> None:
    """Queue advisory work only after its pending review flag is committed."""
    payload = result.get("assessment_payload")
    if not payload or flag.status != FlaggedObject.FLAG_PENDING:
        return
    flag_id, expected_notes = flag.pk, flag.notes
    notes_digest = sha256(expected_notes.encode()).hexdigest()
    content_digest = _assessment_digest(payload)

    def publish_assessment():
        try:
            assess_uncertain_spam.delay(flag_id, notes_digest, content_digest)
        except OperationalError:
            log.warning("Could not queue the advisory spam assessment for flag %s.", flag_id)
            FlaggedObject.objects.filter(
                pk=flag_id, status=FlaggedObject.FLAG_PENDING, notes=expected_notes
            ).update(
                notes=expected_notes + "\n" + _("Advisory spam assessment could not be queued.")
            )

    transaction.on_commit(publish_assessment)


@shared_task_with_retry
@skip_if_read_only_mode
def assess_uncertain_spam(flag_id: int, notes_digest: str, content_digest: str) -> None:
    """Add an independent assessment without reversing or overwriting moderation."""
    flag = (
        FlaggedObject.objects.filter(pk=flag_id, status=FlaggedObject.FLAG_PENDING)
        .select_related("content_type")
        .first()
    )
    if (
        not flag
        or sha256(flag.notes.encode()).hexdigest() != notes_digest
        or not (content := flag.content_object)
    ):
        return
    expected_notes = flag.notes
    match (flag.content_type.app_label, flag.content_type.model):
        case ("questions", "question"):
            payload = question_payload(content)
        case ("customercare", "supportticket"):
            payload = ticket_payload(content)
        case _:
            return
    if _assessment_digest(payload) != content_digest:
        return

    assessment = assess_spam(payload)
    lines = [
        _("Advisory spam assessment ({model})").format(model=settings.SPAM_ASSESSMENT_MODEL),
        _("Suggested verdict: {verdict}").format(verdict=assessment["verdict"]),
        _("Spam signals:"),
        *[f"- {signal}" for signal in assessment["spam_signals"]],
        _("Legitimate support signals:"),
        *[f"- {signal}" for signal in assessment["legitimate_signals"]],
        _("Remaining uncertainty: {uncertainty}").format(uncertainty=assessment["uncertainty"]),
    ]
    FlaggedObject.objects.filter(
        pk=flag_id, status=FlaggedObject.FLAG_PENDING, notes=expected_notes
    ).update(notes=f"{expected_notes}\n\n" + "\n".join(lines))


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
@skip_if_read_only_mode
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

    sumo_bot = Profile.get_sumo_bot()
    stale_flags = (
        FlaggedObject.objects.filter(
            status=FlaggedObject.FLAG_PENDING,
            reason=FlaggedObject.REASON_CONTENT_MODERATION,
            content_type=ContentType.objects.get_for_model(Question),
        )
        .exclude(handled_by=sumo_bot)
        .select_related("creator")[:batch_size]
    )

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
                applied_flag = process_classification_result(question, result)
                processed_count += 1
                if applied_flag.pk is None or applied_flag.pk == flagged_obj.pk:
                    continue
        else:
            flag_note = "Content object no longer exists"

        flagged_obj.status = status
        flagged_obj.notes = flag_note
        flagged_obj.handled_by = Profile.get_sumo_bot()
        flagged_obj.handled = timezone.now()
        flagged_obj.save()

    return f"Processed {processed_count} stale flagged objects"
