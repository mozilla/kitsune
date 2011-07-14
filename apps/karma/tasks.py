from celery.decorators import task
import waffle

from karma.cron import update_top_contributors as _update_top_contributors
from questions.karma_actions import (AnswerAction, AnswerMarkedHelpfulAction,
                                     AnswerMarkedNotHelpfulAction,
                                     FirstAnswerAction, SolutionAction)
from questions.models import Question, AnswerVote
from sumo.utils import chunked, redis_client


@task
def init_karma():
    """Flushes the karma redis backend and populates with fresh data.

    Goes through all questions/answers/votes and save karma actions for them.
    """
    if not waffle.switch_is_active('karma'):
        return

    redis_client('karma').flushdb()

    questions = Question.objects.all()
    for chunk in chunked(questions.values_list('pk', flat=True), 200):
        _process_question_chunk.apply_async(args=[chunk])

    votes = AnswerVote.objects.all()
    for chunk in chunked(votes.values_list('pk', flat=True), 1000):
        _process_answer_vote_chunk.apply_async(args=[chunk])


@task
def update_top_contributors():
    """Updates the top contributor sorted sets."""
    _update_top_contributors()


@task
def _process_question_chunk(data, **kwargs):
    """Save karma data for a chunk of questions."""
    redis = redis_client(name='karma')
    q_qs = Question.objects.select_related('solution').defer('content')
    for question in q_qs.filter(pk__in=data):
        first = True
        a_qs = question.answers.order_by('created').select_related('creator')
        for answer in a_qs.values_list('creator', 'created'):
            AnswerAction(answer[0], answer[1]).save(async=False, redis=redis)
            if first:
                FirstAnswerAction(answer[0], answer[1]).save(async=False,
                                                             redis=redis)
                first = False
        soln = question.solution
        if soln:
            SolutionAction(soln.creator, soln.created).save(async=False,
                                                            redis=redis)


@task
def _process_answer_vote_chunk(data, **kwargs):
    """Save karma data for a chunk of answer votes."""
    redis = redis_client(name='karma')
    v_qs = AnswerVote.objects.select_related('answer')
    for vote in v_qs.filter(pk__in=data):
        if vote.helpful:
            action_class = AnswerMarkedHelpfulAction
        else:
            action_class = AnswerMarkedNotHelpfulAction
        action_class(vote.answer.creator_id, vote.created).save(async=False,
                                                                redis=redis)
