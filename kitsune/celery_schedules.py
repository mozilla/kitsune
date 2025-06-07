from celery.schedules import crontab

from kitsune.tasks import (
    auto_archive_old_questions,
    cache_most_unhelpful_kb_articles,
    cleanup_expired_users,
    cleanup_mail,
    cleanup_old_account_events,
    cohort_analysis,
    enqueue_lag_monitor_task,
    fix_current_revisions,
    generate_missing_share_links,
    rebuild_kb,
    reload_question_traffic_stats,
    reload_wiki_traffic_stats,
    report_employee_answers,
    reindex_es,
    send_queued_mail,
    send_welcome_emails,
    send_weekly_ready_for_review_digest,
    update_contributor_metrics,
    update_l10n_coverage_metrics,
    update_l10n_contributor_metrics,
    update_l10n_metric,
    update_product_details,
    update_top_contributors,
    update_weekly_votes,
)

# Every 10 minutes
CELERY_BEAT_SCHEDULE = {
    "enqueue-lag-monitor-task": {
        "task": enqueue_lag_monitor_task.name,
        "schedule": crontab(minute="*/10"),
    },
    # Every 15 minutes
    "send-queued-mail": {
        "task": send_queued_mail.name,
        "schedule": crontab(minute="*/15"),
    },
    # Every hour at minute 30
    "send-welcome-emails": {
        "task": send_welcome_emails.name,
        "schedule": crontab(minute="30"),
    },
    # Every hour at minute 45
    "reindex-es": {
        "task": reindex_es.name,
        "schedule": crontab(minute="45"),
    },
    # Every 6 hours at minute 00
    "update-product-details": {
        "task": update_product_details.name,
        "schedule": crontab(hour="*/6", minute="00"),
    },
    # Every 6 hours at minute 20
    "generate-missing-share-links": {
        "task": generate_missing_share_links.name,
        "schedule": crontab(hour="*/6", minute="20"),
    },
    # Every Sunday at 12:00
    "cleanup-mail": {
        "task": cleanup_mail.name,
        "schedule": crontab(hour="12", minute="0", day_of_week="0"),
    },
    # Every Sunday at 00:00
    "rebuild-kb": {
        "task": rebuild_kb.name,
        "schedule": crontab(hour="00", minute="00", day_of_week="0"),
    },
    # Every Sunday at 00:42
    "update-top-contributors": {
        "task": update_top_contributors.name,
        "schedule": crontab(hour="00", minute="42", day_of_week="0"),
    },
    # Every Sunday at 01:00
    "update-l10n-coverage-metrics": {
        "task": update_l10n_coverage_metrics.name,
        "schedule": crontab(hour="01", minute="00", day_of_week="0"),
    },
    # Every Sunday at 01:11
    "report-employee-answers": {
        "task": report_employee_answers.name,
        "schedule": crontab(hour="01", minute="11", day_of_week="0"),
    },
    # Every Sunday at 01:40
    "update-weekly-votes": {
        "task": update_weekly_votes.name,
        "schedule": crontab(hour="01", minute="40", day_of_week="0"),
    },
    # Every Sunday at 03:00
    "update-contributor-metrics": {
        "task": update_contributor_metrics.name,
        "schedule": crontab(hour="03", minute="00", day_of_week="0"),
    },
    # Every day at 04:00
    "auto-archive-old-questions": {
        "task": auto_archive_old_questions.name,
        "schedule": crontab(hour="04", minute="00"),
    },
    # Every day at 10:00
    "update-l10n-metric": {
        "task": update_l10n_metric.name,
        "schedule": crontab(hour="10", minute="00"),
    },
    # Every day at 16:00
    "reload-wiki-traffic-stats": {
        "task": reload_wiki_traffic_stats.name,
        "schedule": crontab(hour="16", minute="00"),
    },
    # Every day at 21:00
    "cache-most-unhelpful-kb-articles": {
        "task": cache_most_unhelpful_kb_articles.name,
        "schedule": crontab(hour="21", minute="00"),
    },
    # Every day at 23:00
    "reload-question-traffic-stats": {
        "task": reload_question_traffic_stats.name,
        "schedule": crontab(hour="23", minute="00"),
    },
    # Every Friday at 04:00
    "send-weekly-ready-for-review-digest": {
        "task": send_weekly_ready_for_review_digest.name,
        "schedule": crontab(hour="04", minute="00", day_of_week="5"),
    },
    # Every Monday at 00:30
    "cohort-analysis": {
        "task": cohort_analysis.name,
        "schedule": crontab(hour="00", minute="30", day_of_week="1"),
    },
    # First day of every month at 00:30
    "update-l10n-contributor-metrics": {
        "task": update_l10n_contributor_metrics.name,
        "schedule": crontab(hour="00", minute="30", day_of_month="1"),
    },
    # Every Sunday at 02:00
    "cleanup-old-account-events": {
        "task": cleanup_old_account_events.name,
        "schedule": crontab(hour="02", minute="00", day_of_week="0"),
    },
    # Every Sunday at 03:00
    "cleanup-expired-users": {
        "task": cleanup_expired_users.name,
        "schedule": crontab(hour="03", minute="00", day_of_week="0"),
    },
    # Every Sunday at 00:00
    "fix-current-revisions": {
        "task": fix_current_revisions.name,
        "schedule": crontab(hour="00", minute="00", day_of_week="0"),
    },
    # Every 4 hours, 15 minutes after the hour
    "process-unprocessed-account-events": {
        "task": "kitsune.users.tasks.process_unprocessed_account_events",
        "schedule": crontab(minute="15", hour="*/4"),
        "args": [1],
    },
}
