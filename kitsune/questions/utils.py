import logging
import re

from django.conf import settings

from kitsune.questions.models import Answer, Question

log = logging.getLogger('k.questions')
block_regex = re.compile(settings.QUESTION_BLOCK_REGEX) if settings.QUESTION_BLOCK_REGEX else None


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


def get_mobile_product_from_ua(user_agent):

    ua = user_agent.lower()

    if "rocket" in ua:
        return "firefox-lite"
    elif "fxios" in ua:
        return "ios"

    # android
    try:
        # We are using firefox instead of Firefox as lower() has been applied to the UA
        mobile_client = re.search(
            r"firefox/(?P<version>\d+)\.\d+", ua
        ).groupdict()
    except AttributeError:
        return None
    else:
        if int(mobile_client["version"]) >= 69:
            return "firefox-preview"
        return "mobile"


def in_blocklist(content):
    return block_regex and block_regex.search(content)
