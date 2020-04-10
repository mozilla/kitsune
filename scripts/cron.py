from __future__ import print_function

import datetime
import os
import sys
from subprocess import check_call

import babis
from apscheduler.schedulers.blocking import BlockingScheduler
from django.conf import settings

MANAGE = os.path.join(settings.ROOT, 'manage.py')
schedule = BlockingScheduler()


def call_command(command):
    check_call('python {0} {1}'.format(MANAGE, command), shell=True)


class scheduled_job(object):
    """Decorator for scheduled jobs. Takes same args as apscheduler.schedule_job."""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.skip = self.kwargs.pop('skip', False)

    def __call__(self, fn):
        self.name = fn.__name__
        if self.skip:
            self.log('Skipped, not registered.')
            return None
        self.callback = fn
        schedule.add_job(self.run, id=self.name, *self.args, **self.kwargs)
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


# Every 10 minutes.
@scheduled_job('cron', month='*', day='*', hour='*', minute='*/10',
               max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_ENQUEUE_LAG_MONITOR_TASK)
def job_enqueue_lag_monitor_task():
    call_command('enqueue_lag_monitor_task')


# Every hour.
@scheduled_job('cron', month='*', day='*', hour='*', minute='30',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_SEND_WELCOME_EMAILS)
def job_send_welcome_emails():
    call_command('send_welcome_emails')


# Every hour.
@scheduled_job('cron', month='*', day='*', hour='*', minute='00',
               max_instances=1, coalesce=True, skip=(settings.READ_ONLY or settings.STAGE))
@babis.decorator(ping_after=settings.DMS_PROCESS_EXIT_SURVEYS)
def job_process_exit_surveys():
    call_command('process_exit_surveys')


@scheduled_job('cron', month='*', day='*', hour='*', minute='45', max_instances=1, coalesce=True)
@babis.decorator(ping_after=settings.DMS_REINDEX)
def job_reindex():
    # Look back 90 minutes for new items to avoid racing conditions between
    # cron execution and db updates.
    call_command('esreindex --minutes-ago 90')


# Every 6 hours.
@scheduled_job('cron', month='*', day='*', hour='*/6', minute='00',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_UPDATE_PRODUCT_DETAILS)
def job_update_product_details():
    call_command('update_product_details')


@scheduled_job('cron', month='*', day='*', hour='*/6', minute='20',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_GENERATE_MISSING_SHARE_LINKS)
def job_generate_missing_share_links():
    call_command('generate_missing_share_links')


# Once per day.
@scheduled_job('cron', month='*', day='*', hour='00', minute='00',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_REBUILD_KB)
def job_rebuild_kb():
    call_command('rebuild_kb')


@scheduled_job('cron', month='*', day='*', hour='00', minute='42',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_UPDATE_TOP_CONTRIBUTORS)
def job_update_top_contributors():
    call_command('update_top_contributors')


@scheduled_job('cron', month='*', day='*', hour='01', minute='00',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_UPDATE_L10N_COVERAGE_METRICS)
def job_update_l10n_coverage_metrics():
    call_command('update_l10n_coverage_metrics')


@scheduled_job('cron', month='*', day='*', hour='01', minute='00',
               max_instances=1, coalesce=True, skip=(settings.READ_ONLY or settings.STAGE))
@babis.decorator(ping_after=settings.DMS_CALCULATE_CSAT_METRICS)
def job_calculate_csat_metrics():
    call_command('calculate_csat_metrics')


@scheduled_job('cron', month='*', day='*', hour='01', minute='11',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_REPORT_EMPLOYEE_ANSWERS)
def job_report_employee_answers():
    call_command('report_employee_answers')


@scheduled_job('cron', month='*', day='*', hour='01', minute='30',
               max_instances=1, coalesce=True, skip=settings.STAGE)
@babis.decorator(ping_after=settings.DMS_REINDEX_USERS_THAT_CONTRIBUTED_YESTERDAY)
def job_reindex_users_that_contributed_yesterday():
    call_command('reindex_users_that_contributed_yesterday')


@scheduled_job('cron', month='*', day='*', hour='01', minute='40',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_UPDATE_WEEKLY_VOTES)
def job_update_weekly_votes():
    call_command('update_weekly_votes')


# @scheduled_job('cron', month='*', day='*', hour='02', minute='00', max_instances=1, coalesce=True)
# @babis.decorator(ping_after=settings.DMS_UPDATE_SEARCH_CTR_METRIC)
# def job_update_search_ctr_metric():
#     call_command('update_search_ctr_metric')


@scheduled_job('cron', month='*', day='*', hour='03', minute='00',
               max_instances=1, coalesce=True, skip=(settings.READ_ONLY or settings.STAGE))
@babis.decorator(ping_after=settings.DMS_UPDATE_CONTRIBUTOR_METRICS)
def job_update_contributor_metrics():
    call_command('update_contributor_metrics')


@scheduled_job('cron', month='*', day='*', hour='04', minute='00',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_AUTO_ARCHIVE_OLD_QUESTIONS)
def job_auto_archive_old_questions():
    call_command('auto_archive_old_questions')


@scheduled_job('cron', month='*', day='*', hour='07', minute='00',
               max_instances=1, coalesce=True, skip=(settings.READ_ONLY or settings.STAGE))
@babis.decorator(ping_after=settings.DMS_SURVEY_RECENT_ASKERS)
def job_survey_recent_askers():
    call_command('survey_recent_askers')


# @scheduled_job('cron', month='*', day='*', hour='09', minute='00', max_instances=1, coalesce=True)
# @babis.decorator(ping_after=settings.DMS_UPDATE_VISITORS_METRIC)
# def job_update_visitors_metric():
#     call_command('update_visitors_metric')


@scheduled_job('cron', month='*', day='*', hour='10', minute='00',
               max_instances=1, coalesce=True, skip=(settings.READ_ONLY or settings.STAGE))
@babis.decorator(ping_after=settings.DMS_UPDATE_L10N_METRIC)
def job_update_l10n_metric():
    call_command('update_l10n_metric')


@scheduled_job('cron', month='*', day='*', hour='16', minute='00',
               max_instances=1, coalesce=True, skip=(settings.READ_ONLY or settings.STAGE))
@babis.decorator(ping_after=settings.DMS_RELOAD_WIKI_TRAFFIC_STATS)
def job_reload_wiki_traffic_stats():
    call_command('reload_wiki_traffic_stats')


@scheduled_job('cron', month='*', day='*', hour='21', minute='00',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_CACHE_MOST_UNHELPFUL_KB_ARTICLES)
def job_cache_most_unhelpful_kb_articles():
    call_command('cache_most_unhelpful_kb_articles')


@scheduled_job('cron', month='*', day='*', hour='23', minute='00',
               max_instances=1, coalesce=True, skip=(settings.READ_ONLY or settings.STAGE))
@babis.decorator(ping_after=settings.DMS_RELOAD_QUESTION_TRAFFIC_STATS)
def job_reload_question_traffic_stats():
    call_command('reload_question_traffic_stats')


@scheduled_job('cron', month='*', day='*', hour='04', minute='00', day_of_week=5,
               max_instances=1, coalesce=True, skip=(settings.READ_ONLY or settings.STAGE))
@babis.decorator(ping_after=settings.DMS_SEND_WEEKLY_READY_FOR_REVIEW_DIGEST)
def job_send_weekly_ready_for_review_digest():
    call_command('send_weekly_ready_for_review_digest')


@scheduled_job('cron', month='*', day='*', hour='00', minute='00', day_of_week=0,
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_FIX_CURRENT_REVISIONS)
def job_fix_current_revisions():
    call_command('fix_current_revisions')


@scheduled_job('cron', month='*', day='*', hour='00', minute='30', day_of_week=1,
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_COHORT_ANALYSIS)
def job_cohort_analysis():
    call_command('cohort_analysis')


# Once per month
@scheduled_job('cron', month='*', day='1', hour='00', minute='30',
               max_instances=1, coalesce=True, skip=settings.READ_ONLY)
@babis.decorator(ping_after=settings.DMS_UPDATE_L10N_CONTRIBUTOR_METRICS)
def job_update_l10n_contributor_metrics():
    call_command('update_l10n_contributor_metrics')


def run():
    try:
        schedule.start()
    except (KeyboardInterrupt, SystemExit):
        pass
