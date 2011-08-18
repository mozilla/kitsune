#!/usr/bin/env python
import os
from string import Template


CRONS = {}

COMMON = {
    'MANAGE': '/usr/bin/python26 manage.py',
    'CRON': '$DJANGO cron',
    'DJANGO': 'cd $KITSUNE; $MANAGE',
}

CRONS['support'] = {
    'KITSUNE': '/data/www/support.allizom.org/kitsune',
}

CRONS['support-release'] = {
    'KITSUNE': '/data/www/support-release.allizom.org/kitsune',
}

CRONS['prod'] = {
    'KITSUNE': '/data/www/support.mozilla.com/kitsune',
}

# Update each dict with the values from common.
for key, dict_ in CRONS.items():
    dict_.update(COMMON)

# Do any interpolation inside the keys.
for dict_ in CRONS.values():
    while 1:
        changed = False
        for key, val in dict_.items():
            new = Template(val).substitute(dict_)
            if new != val:
                changed = True
                dict_[key] = new
        if not changed:
            break


cron = """\
#
# !!AUTO-GENERATED!!  Edit scripts/crontab/make-crons.py instead.
#

MAILTO=cron-sumo@mozilla.com

HOME = /tmp

# Every minute!
* * * * * $CRON collect_tweets
* * * * * $CRON get_queue_status

# Every hour.
42 * * * * $DJANGO cleanup

# Every 2 hours.
1 */2 * * * $CRON calculate_related_documents

# Every 6 hours.
0 */6 * * * $DJANGO update_product_details -q > /dev/null
10 */6 * * * $CRON rebuild_kb
30 */6 * * * $CRON get_customercare_stats
40 */6 * * * $CRON purge_tweets
50 */6 * * * $CRON cache_top_contributors

# Once per day.
0 16 * * * $CRON reload_wiki_traffic_stats
40 1 * * * $CRON update_weekly_votes
42 0 * * * $CRON update_top_contributors

# Twice per week.
#05 01 * * 1,4 $CRON update_weekly_votes

# Once per week.
21 03 * * 3 $DJANGO purge_hashes

MAILTO=root
"""


def main():
    for key, vals in CRONS.items():
        path = os.path.join(os.path.dirname(__file__), key)
        open(path, 'w').write(Template(cron).substitute(vals))


if __name__ == '__main__':
    main()
