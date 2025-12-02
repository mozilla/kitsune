from celery.schedules import crontab

# Periodic tasks for all of the environments: dev, stage, and prod.
PERIODIC_TASKS_ALL = {
    # Community Periodic Tasks
    # Every hour at 30 minutes past.
    "send_welcome_emails": {
        "task": "kitsune.community.tasks.send_welcome_emails",
        "schedule": crontab(minute="30"),
    },
    # Dashboards Periodic Tasks
    # Daily at 21:00.
    "cache_most_unhelpful_kb_articles": {
        "task": "kitsune.dashboards.tasks.cache_most_unhelpful_kb_articles",
        "schedule": crontab(hour="21", minute="0"),
    },
    # On the 1st of every month at 00:30.
    "update_l10n_contributor_metrics": {
        "task": "kitsune.dashboards.tasks.update_l10n_contributor_metrics",
        "schedule": crontab(day_of_month="1", hour="0", minute="30"),
    },
    # Daily at 01:00.
    "update_l10n_coverage_metrics": {
        "task": "kitsune.dashboards.tasks.update_l10n_coverage_metrics",
        "schedule": crontab(hour="1", minute="0"),
    },
    # Karma Periodic Tasks
    # Daily at 00:42.
    "update_top_contributors": {
        "task": "kitsune.karma.tasks.update_top_contributors",
        "schedule": crontab(hour="0", minute="42"),
    },
    # KPI Periodic Tasks
    # Every Monday at 00:30.
    "cohort_analysis": {
        "task": "kitsune.kpi.tasks.cohort_analysis",
        "schedule": crontab(hour="0", minute="30", day_of_week="1"),
    },
    # LLM Periodic Tasks
    # Daily at 02:00.
    "process_moderation_queue": {
        "task": "kitsune.llm.tasks.process_moderation_queue",
        "schedule": crontab(hour="2", minute="0"),
    },
    # Products Periodic Tasks
    # Every 6 hours at 00 minutes past.
    "update_product_details": {
        "task": "kitsune.products.tasks.update_product_details",
        "schedule": crontab(hour="*/6", minute="0"),
    },
    # Every 6 hours at 10 minutes past.
    "sync_product_versions": {
        "task": "kitsune.products.tasks.sync_product_versions",
        "schedule": crontab(hour="*/6", minute="10"),
    },
    # Customer Care Periodic Tasks
    # Daily at 03:30.
    "auto_reject_old_zendesk_spam": {
        "task": "kitsune.customercare.tasks.auto_reject_old_zendesk_spam",
        "schedule": crontab(hour="3", minute="30"),
    },
    # Questions Periodic Tasks
    # Daily at 04:00.
    "auto_archive_old_questions": {
        "task": "kitsune.questions.tasks.auto_archive_old_questions",
        "schedule": crontab(hour="4", minute="0"),
    },
    # Every Sun, Tue, Thu at 22:00.
    "cleanup_old_spam": {
        "task": "kitsune.questions.tasks.cleanup_old_spam",
        "schedule": crontab(hour="22", minute="0", day_of_week="0,2,4"),
    },
    # Daily at 01:11.
    "report_employee_answers": {
        "task": "kitsune.questions.tasks.report_employee_answers",
        "schedule": crontab(hour="1", minute="11"),
    },
    # Daily at 01:40.
    "update_weekly_votes": {
        "task": "kitsune.questions.tasks.update_weekly_votes",
        "schedule": crontab(hour="1", minute="40"),
    },
    # SUMO Periodic Tasks
    # Every 10 minutes.
    "enqueue_lag_monitor": {
        "task": "kitsune.sumo.tasks.enqueue_lag_monitor",
        "schedule": crontab(minute="*/10"),
    },
    # Every 15 minutes.
    "process_queued_mail": {
        "task": "kitsune.sumo.tasks.process_queued_mail",
        "schedule": crontab(minute="*/15"),
    },
    # Every Sunday at 12:00.
    "remove_expired_mail": {
        "task": "kitsune.sumo.tasks.remove_expired_mail",
        "schedule": crontab(hour="12", minute="0", day_of_week="0"),
    },
    # Users Periodic Tasks
    # Every Sunday at 03:00.
    "cleanup_expired_users": {
        "task": "kitsune.users.tasks.cleanup_expired_users",
        "schedule": crontab(hour="3", minute="0", day_of_week="0"),
    },
    # Every Sunday at 02:00.
    "cleanup_old_account_events": {
        "task": "kitsune.users.tasks.cleanup_old_account_events",
        "schedule": crontab(hour="2", minute="0", day_of_week="0"),
    },
    # Every 4 hours at 15 minutes past.
    "reprocess_failed_account_events": {
        "task": "kitsune.users.tasks.process_unprocessed_account_events",
        "schedule": crontab(hour="*/4", minute="15"),
        "kwargs": {"within_hours": 24},
    },
    # Wiki Periodic Tasks
    # Every 4 hours at 00 minutes past.
    "create_missing_translations": {
        "task": "kitsune.wiki.tasks.create_missing_translations",
        "schedule": crontab(hour="*/4", minute="0"),
    },
    # Every Sunday at 00:00.
    "fix_current_revisions": {
        "task": "kitsune.wiki.tasks.fix_current_revisions",
        "schedule": crontab(hour="0", minute="0", day_of_week="0"),
    },
    # Every 4 hours at 30 minutes past.
    "process_stale_translations": {
        "task": "kitsune.wiki.tasks.process_stale_translations",
        "schedule": crontab(hour="*/4", minute="30"),
    },
    # Every hour at 55 minutes past.
    "publish_pending_translations": {
        "task": "kitsune.wiki.tasks.publish_pending_translations",
        "schedule": crontab(minute="55"),
    },
    # Daily at 00:00.
    "rebuild_kb": {
        "task": "kitsune.wiki.tasks.run_rebuild_kb",
        "schedule": crontab(hour="0", minute="0"),
    },
}

# Periodic tasks only for the prod environment.
PERIODIC_TASKS_PRODUCTION_ONLY = {
    # Wiki Periodic Tasks
    # Daily at 16:00.
    "reload_wiki_traffic_stats": {
        "task": "kitsune.dashboards.tasks.reload_wiki_traffic_stats",
        "schedule": crontab(hour="16", minute="0"),
    },
    # KPI Periodic Tasks
    # Daily at 03:00.
    "update_contributor_metrics": {
        "task": "kitsune.kpi.tasks.update_contributor_metrics",
        "schedule": crontab(hour="3", minute="0"),
    },
    # Daily at 10:00.
    "update_l10n_metric": {
        "task": "kitsune.kpi.tasks.update_l10n_metric",
        "schedule": crontab(hour="10", minute="0"),
    },
    # Questions Periodic Tasks
    # Daily at 23:00.
    "reload_question_traffic_stats": {
        "task": "kitsune.questions.tasks.reload_question_traffic_stats",
        "schedule": crontab(hour="23", minute="0"),
    },
    # Wiki Periodic Tasks
    # Every 6 hours at 20 minutes past.
    "generate_missing_share_links": {
        "task": "kitsune.wiki.tasks.generate_missing_share_links",
        "schedule": crontab(hour="*/6", minute="20"),
    },
    # Every Friday at 04:00.
    "send_weekly_ready_for_review_digest": {
        "task": "kitsune.wiki.tasks.send_weekly_ready_for_review_digest",
        "schedule": crontab(hour="4", minute="0", day_of_week="5"),
    },
}
