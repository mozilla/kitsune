import waffle
from celery import shared_task

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
                "Automatically flagged for topic moderation:"
                " auto-question-classifier is disabled"
            ),
        )
