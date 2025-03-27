import datetime
import os
from subprocess import check_call
import waffle

from celery import shared_task
from django.conf import settings
from django.utils import timezone

# Get the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANAGE = os.path.join(ROOT, "manage.py")


def call_command(command):
    check_call("python {0} {1}".format(MANAGE, command), shell=True)


@shared_task
def enqueue_lag_monitor_task():
    call_command("enqueue_lag_monitor_task")


@shared_task
def send_welcome_emails():
    if not settings.READ_ONLY:
        call_command("send_welcome_emails")


@shared_task
def send_queued_mail():
    if not settings.READ_ONLY:
        call_command("send_queued_mail_async")


@shared_task
def cleanup_mail():
    if not settings.READ_ONLY:
        call_command("cleanup_mail")


@shared_task
def reindex_es():
    if settings.READ_ONLY:
        # Index items newer than 90 minutes old in ES
        after = (timezone.now() - datetime.timedelta(minutes=90)).isoformat()
        call_command("es_reindex --updated-after {}".format(after))


@shared_task
def update_product_details():
    if not settings.READ_ONLY:
        call_command("update_product_details")


@shared_task
def generate_missing_share_links():
    if not settings.READ_ONLY and not settings.STAGE:
        call_command("generate_missing_share_links")


@shared_task
def rebuild_kb():
    if not settings.READ_ONLY:
        call_command("rebuild_kb")


@shared_task
def update_top_contributors():
    if not settings.READ_ONLY:
        call_command("update_top_contributors")


@shared_task
def update_l10n_coverage_metrics():
    if not settings.READ_ONLY:
        call_command("update_l10n_coverage_metrics")


@shared_task
def report_employee_answers():
    if not settings.READ_ONLY:
        call_command("report_employee_answers")


@shared_task
def update_weekly_votes():
    if not settings.READ_ONLY:
        call_command("update_weekly_votes")


@shared_task
def update_contributor_metrics():
    if not settings.READ_ONLY and not settings.STAGE:
        call_command("update_contributor_metrics")


@shared_task
def auto_archive_old_questions():
    if not settings.READ_ONLY:
        call_command("auto_archive_old_questions")


@shared_task
def update_l10n_metric():
    if not settings.READ_ONLY and not settings.STAGE:
        call_command("update_l10n_metric")


@shared_task
def reload_wiki_traffic_stats():
    if not settings.READ_ONLY and not settings.STAGE:
        call_command("reload_wiki_traffic_stats")


@shared_task
def cache_most_unhelpful_kb_articles():
    if not settings.READ_ONLY:
        call_command("cache_most_unhelpful_kb_articles")


@shared_task
def reload_question_traffic_stats():
    if not settings.READ_ONLY and not settings.STAGE:
        call_command("reload_question_traffic_stats")


@shared_task
def send_weekly_ready_for_review_digest():
    if not settings.READ_ONLY and not settings.STAGE:
        call_command("send_weekly_ready_for_review_digest")


@shared_task
def fix_current_revisions():
    if not settings.READ_ONLY:
        call_command("fix_current_revisions")


@shared_task
def cohort_analysis():
    if not settings.READ_ONLY:
        call_command("cohort_analysis")


@shared_task
def update_l10n_contributor_metrics():
    if not settings.READ_ONLY:
        call_command("update_l10n_contributor_metrics")


@shared_task
def cleanup_old_account_events():
    if not settings.READ_ONLY:
        call_command("cleanup_old_account_events")


@shared_task
def cleanup_expired_users():
    if not settings.READ_ONLY and waffle.switch_is_active("cleanup-expired-users"):
        call_command("cleanup_expired_users")
