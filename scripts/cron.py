from __future__ import print_function
import datetime
import os
import sys
from subprocess import check_call

from django.conf import settings

import babis
from apscheduler.schedulers.blocking import BlockingScheduler


MANAGE = os.path.join(settings.ROOT, 'manage.py')
schedule = BlockingScheduler()


def call_command(command):
    check_call('python {0} {1}'.format(MANAGE, command), shell=True)


class scheduled_job(object):
    """Decorator for scheduled jobs. Takes same args as apscheduler.schedule_job."""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, fn):
        job_name = fn.__name__
        self.name = job_name
        self.callback = fn
        schedule.add_job(self.run, id=job_name, *self.args, **self.kwargs)
        self.log('Registered.')
        return self.run

    def run(self):
        self.log('starting')
        try:
            self.callback()
        except Exception as e:
            self.log('CRASHED: {}'.format(e))
            raise
        else:
            self.log('finished successfully')

    def log(self, message):
        msg = '[{}] Clock job {}@{}: {}'.format(
            datetime.datetime.utcnow(), self.name,
            settings.PLATFORM_NAME, message)
        print(msg, file=sys.stderr)


class skip_read_only(object):
    """Decorator that skips wrapped functions when READ_ONLY=True"""
    def __call__(self, fn):
        self.name = fn.__name__
        self.callback = fn
        return self.run

    def run(self):
        if settings.READ_ONLY:
            print('Skipping {} because READ_ONLY=True'.format(self.name))
            return

        self.callback()


# Every 10 minutes.
@scheduled_job('cron', month='*', day='*', hour='*', minute='*/10', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_ENQUEUE_LAG_MONITOR_TASK)
def job_enqueue_lag_monitor_task():
    call_command('cron enqueue_lag_monitor_task')


# Every hour.
@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='*', minute='30', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_SEND_WELCOME_EMAILS)
def job_send_welcome_emails():
    call_command('cron send_welcome_emails')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='*', minute='59', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_ESCALATE_QUESTIONS)
def job_escalate_questions():
    call_command('cron escalate_questions')


# Every 6 hours.
@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='*/6', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_UPDATE_PRODUCT_DETAILS)
def job_update_product_details():
    call_command('update_product_details')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='*/6', minute='20', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_GENERATE_MISSING_SHARE_LINKS)
def job_generate_missing_share_links():
    call_command('cron generate_missing_share_links')


# Once per day.
@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='00', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_REBUILD_KB)
def job_rebuild_kb():
    call_command('cron rebuild_kb')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='00', minute='42', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_UPDATE_TOP_CONTRIBUTORS)
def job_update_top_contributors():
    call_command('cron update_top_contributors')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='01', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_UPDATE_L10N_COVERAGE_METRICS)
def job_update_l10n_coverage_metrics():
    call_command('cron update_l10n_coverage_metrics')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='01', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_CALCULATE_CSAT_METRICS)
def job_calculate_csat_metrics():
    call_command('cron calculate_csat_metrics')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='01', minute='11', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_REPORT_EMPLOYEE_ANSWERS)
def job_report_employee_answers():
    call_command('cron report_employee_answers')


@scheduled_job('cron', month='*', day='*', hour='01', minute='30', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_REINDEX_USERS_THAT_CONTRIBUTED_YESTERDAY)
def job_reindex_users_that_contributed_yesterday():
    call_command('cron reindex_users_that_contributed_yesterday')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='01', minute='40', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_UPDATE_WEEKLY_VOTES)
def job_update_weekly_votes():
    call_command('cron update_weekly_votes')


# @scheduled_job('cron', month='*', day='*', hour='02', minute='00', max_instances=1, coalesce=True)
# @babis.decorator(ping_after=settings.DMS_UPDATE_SEARCH_CTR_METRIC)
# def job_update_search_ctr_metric():
#     call_command('cron update_search_ctr_metric')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='02', minute='47', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_REMOVE_EXPIRED_REGISTRATION_PROFILES)
def job_remove_expired_registration_profiles():
    call_command('cron remove_expired_registration_profiles')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='03', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_UPDATE_CONTRIBUTOR_METRICS)
def job_update_contributor_metrics():
    call_command('cron update_contributor_metrics')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='04', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_AUTO_ARCHIVE_OLD_QUESTIONS)
def job_auto_archive_old_questions():
    call_command('cron auto_archive_old_questions')


@scheduled_job('cron', month='*', day='*', hour='05', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_REINDEX_KB)
def job_reindex_kb():
    call_command('cron reindex_kb')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='06', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_PROCESS_EXIT_SURVEYS)
def job_process_exit_surveys():
    call_command('cron process_exit_surveys')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='07', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_SURVEY_RECENT_ASKERS)
def job_survey_recent_askers():
    call_command('cron survey_recent_askers')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='08', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_CLEAR_EXPIRED_AUTH_TOKENS)
def job_clear_expired_auth_tokens():
    call_command('cron clear_expired_auth_tokens')


# @scheduled_job('cron', month='*', day='*', hour='09', minute='00', max_instances=1, coalesce=True)
# @babis.decorator(ping_after=settings.DMS_UPDATE_VISITORS_METRIC)
# def job_update_visitors_metric():
#     call_command('cron update_visitors_metric')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='10', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_UPDATE_L10N_METRIC)
def job_update_l10n_metric():
    call_command('cron update_l10n_metric')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='16', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_RELOAD_WIKI_TRAFFIC_STATS)
def job_reload_wiki_traffic_stats():
    call_command('cron reload_wiki_traffic_stats')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='21', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_CACHE_MOST_UNHELPFUL_KB_ARTICLES)
def job_cache_most_unhelpful_kb_articles():
    call_command('cron cache_most_unhelpful_kb_articles')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='23', minute='00', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_RELOAD_QUESTION_TRAFFIC_STATS)
def job_reload_question_traffic_stats():
    call_command('cron reload_question_traffic_stats')


# Once per week
@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='03', minute='21',
               day_of_week=3, max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_PURGE_HASHES)
def job_purge_hashes():
    call_command('purge_hashes')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='04', minute='00',
               day_of_week=5, max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_SEND_WEEKLY_READY_FOR_REVIEW_DIGEST)
def job_send_weekly_ready_for_review_digest():
    call_command('cron send_weekly_ready_for_review_digest')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='00', minute='00',
               day_of_week=0, max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_FIX_CURRENT_REVISIONS)
def job_fix_current_revisions():
    call_command('cron fix_current_revisions')


@skip_read_only()
@scheduled_job('cron', month='*', day='*', hour='00', minute='30',
               day_of_week=1, max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_COHORT_ANALYSIS)
def job_cohort_analysis():
    call_command('cron cohort_analysis')


# Once per month
@skip_read_only()
@scheduled_job('cron', month='*', day='1', hour='00', minute='30', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_UPDATE_L10N_CONTRIBUTOR_METRICS)
def job_update_l10n_contributor_metrics():
    call_command('cron update_l10n_contributor_metrics')


def run():
    try:
        schedule.start()
    except (KeyboardInterrupt, SystemExit):
        pass
