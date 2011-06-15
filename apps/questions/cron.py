from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache

from celery.messaging import establish_connection
import cronjobs

from questions.models import QuestionVote
from questions.tasks import update_question_vote_chunk
from sumo.utils import chunked


@cronjobs.register
def update_weekly_votes():
    """Keep the num_votes_past_week value accurate."""

    recent = datetime.now() - timedelta(days=14)

    q = QuestionVote.objects.filter(created__gte=recent)
    q = q.values_list('question_id', flat=True).distinct()

    with establish_connection() as conn:
        for chunk in chunked(q, 50):
            update_question_vote_chunk.apply_async(args=[chunk],
                                                   connection=conn)


@cronjobs.register
def cache_top_contributors():
    """Compute the top contributors and store in cache."""
    sql = '''SELECT u.*, COUNT(*) AS num_solutions
             FROM auth_user AS u, questions_answer AS a,
                  questions_question AS q
             WHERE u.id = a.creator_id AND a.id = q.solution_id AND
                   a.created >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
             GROUP BY u.id
             ORDER BY num_solutions DESC
             LIMIT 10'''
    users = list(User.objects.raw(sql))
    cache.set(settings.TOP_CONTRIBUTORS_CACHE_KEY, users,
              settings.TOP_CONTRIBUTORS_CACHE_TIMEOUT)
