#
# !!AUTO-GENERATED!!  Edit scripts/crontab/crontab.tpl instead.
#

MAILTO=cron-sumo@mozilla.com

HOME = /tmp

# Each line is minute, hour, day of month, day of week, month.
# Entries are sorted in chronological order.

# Every minute!
* * * * * {{ cron }} collect_tweets

# Every 10 minutes!
*/10 * * * * {{ cron }} enqueue_lag_monitor_task

# Every hour.
30 * * * * {{ cron }} send_welcome_emails
59 * * * * {{ cron }} escalate_questions

# Every 6 hours.
00 */6 * * * {{ django }} update_product_details -q > /dev/null
20 */6 * * * {{ cron }} generate_missing_share_links
40 */6 * * * {{ cron }} purge_tweets

# Once per day.
00 00 * * * {{ cron }} rebuild_kb
42 00 * * * {{ cron }} update_top_contributors
00 01 * * * {{ cron }} update_l10n_coverage_metrics
00 01 * * * {{ cron }} calculate_csat_metrics
11 01 * * * {{ cron }} report_employee_answers
30 01 * * * {{ cron }} reindex_users_that_contributed_yesterday
40 01 * * * {{ cron }} update_weekly_votes
00 02 * * * {{ cron }} update_search_ctr_metric
47 02 * * * {{ cron }} remove_expired_registration_profiles
00 03 * * * {{ cron }} update_contributor_metrics
30 03 * * * {{ cron }} send_postatus_errors
00 04 * * * {{ cron }} auto_archive_old_questions
00 05 * * * {{ cron }} reindex_kb
00 06 * * * {{ cron }} process_exit_surveys
00 07 * * * {{ cron }} survey_recent_askers
00 08 * * * {{ cron }} clear_expired_auth_tokens
00 09 * * * {{ cron }} update_visitors_metric
00 10 * * * {{ cron }} update_l10n_metric
00 16 * * * {{ cron }} reload_wiki_traffic_stats
00 23 * * * {{ cron }} reload_question_traffic_stats
00 21 * * * {{ cron }} cache_most_unhelpful_kb_articles
00 22 * * * {{ cron }} get_customercare_stats
42 22 * * * {{ django }} clearsessions

# Once per week.
21 03 * * 3 {{ django }} purge_hashes
00 04 * * 5 {{ cron }} send_weekly_ready_for_review_digest
00 00 * * 0 {{ cron }} fix_current_revisions
30 00 * * 1 {{ cron }} cohort_analysis

# Once per month.
00 00 1 * * {{ cron }} update_l10n_contributor_metrics

MAILTO=root
