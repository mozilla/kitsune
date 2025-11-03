from celery import shared_task
from django.contrib.auth.models import User

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.utils import process_zendesk_classification_result
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.llm.support.classifiers import classify_zendesk_submission

shared_task_with_retry = shared_task(
    acks_late=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)


@shared_task_with_retry
def zendesk_submission_classifier(submission_id: int) -> None:
    """Classify a support ticket for spam and process the result.

    Always runs the classifier. The waffle switch only controls
    behavior when spam is detected (flag for moderation vs reject).
    """
    try:
        submission = SupportTicket.objects.get(id=submission_id)
    except SupportTicket.DoesNotExist:
        return

    result = classify_zendesk_submission(submission)
    process_zendesk_classification_result(submission, result)


@shared_task
def update_zendesk_user(user_id: int) -> None:
    user = User.objects.get(pk=user_id)
    if user.profile.zendesk_id:
        zendesk = ZendeskClient()
        zendesk.update_user(user)


@shared_task
def update_zendesk_identity(user_id: int, email: str) -> None:
    user = User.objects.get(pk=user_id)
    zendesk_user_id = user.profile.zendesk_id

    # fetch identity id
    if zendesk_user_id:
        zendesk = ZendeskClient()
        zendesk.update_primary_email(zendesk_user_id, email)
