from django.conf import settings
from django.db import transaction, connection

import cronjobs

from dashboards.models import PERIODS, WikiDocumentVisits
from sumo.utils import redis_client


@cronjobs.register
def reload_wiki_traffic_stats():
    transaction.enter_transaction_management()
    transaction.managed(True)

    for period, _ in PERIODS:
        try:
            WikiDocumentVisits.reload_period_from_json(
                     period, WikiDocumentVisits.json_for(period))
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

    # Nice but not necessary when the process is about to exit:
    transaction.leave_transaction_management()


def _get_old_unhelpful():
    old_formatted = {}
    cursor = connection.cursor()

    cursor.execute('SELECT doc_id, yes, no '
        'FROM '
            '(SELECT wiki_revision.document_id as doc_id, '
                'SUM(limitedvotes.helpful) as yes, '
                'SUM(NOT(limitedvotes.helpful)) as no '
            'FROM '
                '(SELECT * FROM wiki_helpfulvote '
                    'WHERE created <= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) '
                    'AND created >= DATE_SUB(DATE_SUB(CURDATE(), '
                        'INTERVAL 1 MONTH), INTERVAL 1 MONTH) '
                ') as limitedvotes '
            'INNER JOIN wiki_revision ON '
                'limitedvotes.revision_id=wiki_revision.id '
            'INNER JOIN wiki_document ON '
                'wiki_document.id=wiki_revision.document_id '
            'WHERE wiki_document.locale="en-US" '
            'GROUP BY doc_id '
            'HAVING no > yes '
            ') as calculated ')

    old_data = cursor.fetchall()

    for data in old_data:
        doc_id = data[0]
        yes = float(data[1])
        no = float(data[2])
        total = yes + no
        if total == 0:
            continue
        old_formatted[doc_id] = {'total': total,
                                 'percentage': yes / total}

    return old_formatted


def _get_current_unhelpful(old_formatted):
    final = {}
    cursor = connection.cursor()

    cursor.execute('SELECT doc_id, yes, no '
        'FROM '
            '(SELECT wiki_revision.document_id as doc_id, '
                'SUM(limitedvotes.helpful) as yes, '
                'SUM(NOT(limitedvotes.helpful)) as no '
            'FROM '
                '(SELECT * FROM wiki_helpfulvote '
                    'WHERE created >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) '
                ') as limitedvotes '
            'INNER JOIN wiki_revision ON '
                'limitedvotes.revision_id=wiki_revision.id '
            'INNER JOIN wiki_document ON '
                'wiki_document.id=wiki_revision.document_id '
            'WHERE wiki_document.locale="en-US" '
            'GROUP BY doc_id '
            'HAVING no > yes '
            ') as calculated ')

    current_data = cursor.fetchall()

    for data in current_data:
        doc_id = data[0]
        yes = float(data[1])
        no = float(data[2])
        total = yes + no
        if total == 0:
            continue
        percentage = yes / total
        if doc_id in old_formatted:
            final[doc_id] = {
                'total': total,
                'currperc': percentage,
                'diffperc': percentage - old_formatted[doc_id]['percentage']
            }
        else:
            final[doc_id] = {
                'total': total,
                'currperc': percentage,
                'diffperc': 0.0
            }

    return final


@cronjobs.register
def cache_most_unhelpful_kb_articles():
    """Calculate and save the most unhelpful KB articles in the past 7 days."""

    REDIS_KEY = settings.HELPFULVOTES_UNHELPFUL_KEY

    old_formatted = _get_old_unhelpful()
    final = _get_current_unhelpful(old_formatted)

    if final == {}:
        return

    def _mean(vals):
        if len(vals) == 0:
            return None
        return sum([float(v) for v in vals]) / len(vals)

    def _bayes_avg(C, m, R, v):
        # Bayesian Average
        # C = mean vote, v = number of votes,
        # R = mean rating, m = minimum votes to list in topranked
        return (C * m + R * v) / (m + v)

    mean = _mean([final[key]['currperc'] for key in final.keys()])

    sorted_final = sorted([(key,
                            final[key]['total'],
                            final[key]['currperc'],
                            final[key]['diffperc'],
                            _bayes_avg(mean, 100, final[key]['currperc'],
                                       final[key]['total']))
                            for key in final.keys()],
                          key=lambda entry: entry[4])  # Sort by Bayesian Avg

    redis = redis_client('helpfulvotes')

    redis.delete(REDIS_KEY)

    max_total = max([b[1] for b in sorted_final])

    for entry in sorted_final:
        redis.rpush(REDIS_KEY, ('%s:%s:%s:%s:%s' %
                                  (entry[0],  # Document ID
                                   entry[1],  # Total Votes
                                   entry[2],  # Current Percentage
                                   entry[3],  # Difference in Percentage
                                   1 - (entry[1] / max_total))))  # Graph Color
