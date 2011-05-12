from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache

import cronjobs

from karma.actions import redis_client, KarmaManager
from questions.karma_actions import (AnswerAction, AnswerMarkedHelpfulAction,
                                     FirstAnswerAction, SolutionAction)
from questions.models import Question, AnswerVote
from questions.tasks import update_question_vote_chunk
from sumo.utils import chunked


@cronjobs.register
def update_weekly_votes():
    """Keep the num_votes_past_week value accurate."""

    recent = datetime.now() - timedelta(days=14)

    q = QuestionVote.objects.filter(created__gte=recent)
    q = q.values_list('question_id', flat=True).order_by('question')
    q = q.distinct()

    for chunk in chunked(q, 50):
        update_question_vote_chunk.apply_async(args=[chunk])


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


@cronjobs.register
def init_karma():
    """Go through all questions/answers/votes and save karma actions for them.
    """
    print 'Starting karma import: {d}'.format(d=datetime.now())
    redis = redis_client('karma')
    q_qs = Question.objects.select_related('solution').defer('content')
    for question in q_qs.all():
        first = True
        a_qs = question.answers.order_by('created').select_related('creator')
        for answer in a_qs.values_list('creator', 'created'):
            AnswerAction(answer[0], answer[1], redis).save()
            if first:
                FirstAnswerAction(answer[0], answer[1], redis).save()
                first = False
        soln = question.solution
        if soln:
            SolutionAction(soln.creator, soln.created, redis).save()

    print 'Finished processing Answers: {d}'.format(d=datetime.now())
    print 'Now processing votes...'

    votes = AnswerVote.objects.filter(helpful=True).select_related('answer')
    for vote in votes:
        AnswerMarkedHelpfulAction(
            vote.answer.creator_id, vote.created, redis).save()

    print 'Finished karma import: {d}'.format(d=datetime.now())


@cronjobs.register
def update_top_contributors():
    """"Update the top contributor lists"""
    print 'Starting top contributor updates: {d}'.format(d=datetime.now())
    kmgr = KarmaManager()
    kmgr.update_top_alltime()
    kmgr.update_top_week()
    print 'Finished top contributor updates: : {d}'.format(d=datetime.now())
