import logging

from statsd import statsd

from kitsune.questions.models import (
    Question, Answer, AnswerMetricsMappingType)
from kitsune.search.es_utils import ES_EXCEPTIONS


log = logging.getLogger('k.questions')


def num_questions(user):
    """Returns the number of questions a user has."""
    return Question.objects.filter(creator=user).count()


def num_answers(user):
    """Returns the number of answers a user has.

    Tries to get the data from ES first.
    """
    try:
        count = (AnswerMetricsMappingType
            .search()
            .filter(creator_id=user.id).count())

        statsd.incr('questions.utils.num_answers.es')
        return count

    except ES_EXCEPTIONS as exc:
        log.exception('num_answers in ES failed.')

    statsd.incr('questions.utils.num_answers.db')
    return Answer.objects.filter(creator=user).count()


def num_solutions(user):
    """Returns the number of solutions a user has.

    Tries to get the data from ES first.
    """
    try:
        count = (AnswerMetricsMappingType
            .search()
            .filter(creator_id=user.id, is_solution=True).count())

        statsd.incr('questions.utils.num_solutions.es')
        return count

    except ES_EXCEPTIONS as exc:
        log.exception('num_solutions in ES failed.')

    statsd.incr('questions.utils.num_solutions.db')
    return Question.objects.filter(solution__creator=user).count()
