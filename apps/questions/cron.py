from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache

import cronjobs

from questions.models import Question, QuestionVote
from questions.tasks import update_question_vote_chunk
from sumo.utils import chunked


@cronjobs.register
def update_weekly_votes():
    """Keep the num_votes_past_week value accurate."""

    # Get all questions (id) with a vote in the last week.
    recent = datetime.now() - timedelta(days=7)
    q = QuestionVote.objects.filter(created__gte=recent)
    q = q.values_list('question_id', flat=True).order_by('question')
    q = q.distinct()
    q_with_recent_votes = list(q)

    # Get all questions with num_votes_past_week > 0
    q = Question.objects.filter(num_votes_past_week__gt=0)
    q = q.values_list('id', flat=True)
    q_with_nonzero_votes = list(q)

    # Union.
    qs_to_update = list(set(q_with_recent_votes + q_with_nonzero_votes))

    # Chunk them for tasks.
    for chunk in chunked(qs_to_update, 50):
        update_question_vote_chunk.apply_async(args=[chunk])


# TODO: remove this and use the karma top list.
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
