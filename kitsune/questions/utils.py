import logging

from kitsune.questions.models import Question, Answer


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


def mark_content_as_spam(user, by_user):
    """Flag all the questions and answers of the user as spam.

    :arg user: the user whose content should be marked as spam
    :arg by_user: the user requesting to mark the content as spam

    """
    for question in Question.objects.filter(creator=user):
        question.mark_as_spam(by_user)

    for answer in Answer.objects.filter(creator=user):
        answer.mark_as_spam(by_user)
