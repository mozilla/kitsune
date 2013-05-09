#
# !!AUTO-GENERATED!!  Edit scripts/crontab/crontab.tpl instead.
#

MAILTO=cron-sumo@mozilla.com

HOME = /tmp

# Every minute!
* * * * * {{ cron }} collect_tweets

# Every hour.
42 * * * * {{ django }} cleanup
30 * * * * {{ cron }} get_customercare_stats

# Every 6 hours.
0 */6 * * * {{ django }} update_product_details -q > /dev/null
10 */6 * * * {{ cron }} rebuild_kb
40 */6 * * * {{ cron }} purge_tweets
50 */6 * * * {{ cron }} cache_top_contributors

# Once per day.
0 16 * * * {{ cron }} reload_wiki_traffic_stats
0 23 * * * {{ cron }} reload_question_traffic_stats
40 1 * * * {{ cron }} update_weekly_votes
42 0 * * * {{ cron }} update_top_contributors
0 21 * * * {{ cron }} cache_most_unhelpful_kb_articles
47 2 * * * {{ cron }} remove_expired_registration_profiles
0 9 * * * {{ cron }} update_visitors_metric
0 10 * * * {{ cron }} update_l10n_metric
0 3 * * * {{ cron }} update_contributor_metrics
0 4 * * * {{ cron }} auto_lock_old_questions
0 5 * * * {{ cron }} reindex_kb

# Twice per week.
#05 01 * * 1,4 {{ cron }} update_weekly_votes

# Once per week.
21 03 * * 3 {{ django }} purge_hashes

MAILTO=root
