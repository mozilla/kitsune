from collections.abc import Callable
import logging
import re

from django.conf import settings

from kitsune.questions.models import Answer, Question
from kitsune.wiki.utils import get_featured_articles as kb_get_featured_articles


REGEX_NON_WINDOWS_HOME_DIR = re.compile(
    r"(?P<home_dir_parent>/(?:user|users|home)/)[^/]+", re.IGNORECASE
)
REGEX_WINDOWS_HOME_DIR = re.compile(
    r"(?P<home_dir_parent>\\(?:user|users|documents and settings|winnt\\profiles)\\)[^\\]+",
    re.IGNORECASE,
)


log = logging.getLogger("k.questions")


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
        re.search(r"firefox/(?P<version>\d+)\.\d+", ua).groupdict()
    except AttributeError:
        return None
    else:
        return "mobile"


def get_featured_articles(product, locale):
    """
    Returns 4 featured articles for the AAQ.

    Will return pinned articles first, then fill randomly from the most visited articles.

    For pinned articles in WIKI_DEFAULT_LANGUAGE, return a localized version if it exists.
    For pinned articles in other locales, return them only if `locale` matches.
    """
    if config := product.aaq_configs.first():
        pinned_articles = [
            localized_article
            for article in config.pinned_articles.filter(
                locale__in=(locale, settings.WIKI_DEFAULT_LANGUAGE)
            )
            if (
                localized_article := article
                if article.locale == locale
                else article.translated_to(locale)
            )
        ]
    else:
        pinned_articles = []

    if len(pinned_articles) < 4:
        return (pinned_articles + kb_get_featured_articles(product=product, locale=locale))[:4]

    return pinned_articles[-4:]


def scrub_home_dir_pii(text: str, mask: str = "<USERNAME>") -> str:
    """
    Cleans the given text of any PII within home directory paths.
    """
    scrubbed_home_dir = rf"\g<home_dir_parent>{mask}"
    return REGEX_NON_WINDOWS_HOME_DIR.sub(
        scrubbed_home_dir, REGEX_WINDOWS_HOME_DIR.sub(scrubbed_home_dir, text)
    )


def scrub(data: dict, scrubbers: list[Callable[[str], str]]) -> dict:
    """
    Clean any text within the given dict with the given scrubbers.
    """
    for key, value in data.items():
        if isinstance(value, dict):
            scrub(value, scrubbers)
        elif isinstance(value, str):
            for scrubber in scrubbers:
                value = scrubber(value)
            data[key] = value
    return data
