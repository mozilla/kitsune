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
    """Returns the number of answers a user has."""
    return Answer.objects.filter(creator=user).count()


def num_solutions(user):
    """Returns the number of solutions a user has."""
    return Question.objects.filter(solution__creator=user).count()
