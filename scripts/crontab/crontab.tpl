#
# !!AUTO-GENERATED!!  Edit scripts/crontab/crontab.tpl instead.
#

MAILTO=cron-sumo@mozilla.com

HOME = /tmp

# Every minute!
* * * * * {{ cron }} collect_tweets

# Every hour.
42 * * * * {{ django }} cleanup

# Every 2 hours.
1 */2 * * * {{ cron }} calculate_related_documents

# Every 6 hours.
0 */6 * * * {{ django }} update_product_details -q > /dev/null
10 */6 * * * {{ cron }} rebuild_kb
30 */6 * * * {{ cron }} get_customercare_stats
40 */6 * * * {{ cron }} purge_tweets
50 */6 * * * {{ cron }} cache_top_contributors

# Once per day.
0 16 * * * {{ cron }} reload_wiki_traffic_stats
40 1 * * * {{ cron }} update_weekly_votes
42 0 * * * {{ cron }} update_top_contributors
0 21 * * * {{ cron }} cache_most_unhelpful_kb_articles
47 2 * * * {{ cron }} remove_expired_registration_profiles
0 3 * * * {{ cron }} update_visitors_metric

# Twice per week.
#05 01 * * 1,4 {{ cron }} update_weekly_votes

# Once per week.
21 03 * * 3 {{ django }} purge_hashes

MAILTO=root
