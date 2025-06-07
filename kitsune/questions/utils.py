import json
import logging
import re
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.backends.base import SessionBase
from sentry_sdk import capture_exception

from kitsune.flagit.models import FlaggedObject
from kitsune.llm.questions.classifiers import ModerationAction
from kitsune.products.models import Product, Topic
from kitsune.questions.models import Answer, Question
from kitsune.users.models import Profile
from kitsune.wiki.utils import get_featured_articles as kb_get_featured_articles
from kitsune.wiki.utils import has_visited_kb

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
                localized_article := (
                    article if article.locale == locale else article.translated_to(locale)
                )
            )
        ]
    else:
        pinned_articles = []

    if len(pinned_articles) < 4:
        return (pinned_articles + kb_get_featured_articles(product=product, locale=locale))[:4]

    return pinned_articles[-4:]


def remove_home_dir_pii(text: str, mask: str = "<USERNAME>") -> str:
    """
    Cleans the given text of any PII within home directory paths.
    """
    scrubbed_home_dir = rf"\g<home_dir_parent>{mask}"
    return REGEX_NON_WINDOWS_HOME_DIR.sub(
        scrubbed_home_dir, REGEX_WINDOWS_HOME_DIR.sub(scrubbed_home_dir, text)
    )


def remove_pii(data: dict) -> None:
    """
    Remove PII from any text within the given dict.
    """
    for key, value in data.items():
        if isinstance(value, dict):
            remove_pii(value)
        elif isinstance(value, str):
            data[key] = remove_home_dir_pii(value)


def get_ga_submit_event_parameters_as_json(
    session: Optional[SessionBase] = None,
    product: Optional[Product] = None,
    topic: Optional[Topic] = None,
) -> str:
    """
    Returns a JSON string of the event parameters for the GA4 "question_submit"
    event, given the session, product, and/or topic.
    """
    data = dict(is_failed_deflection="false")

    if session and product:
        data["is_failed_deflection"] = str(has_visited_kb(session, product, topic=topic)).lower()
        if topic:
            data["topics"] = f"/{topic.slug}/"

    return json.dumps(data)


def flag_question(
    question: Question,
    by_user: User,
    notes: str,
    status: int = FlaggedObject.FLAG_ACCEPTED,
    reason: str = FlaggedObject.REASON_SPAM,
) -> None:
    content_type = ContentType.objects.get_for_model(question)
    flagged_object, created = FlaggedObject.objects.get_or_create(
        content_type=content_type,
        object_id=question.id,
        creator=by_user,
        defaults=dict(
            reason=reason,
            status=status,
            notes=notes,
        ),
    )
    if not created:
        flagged_object.reason = reason
        flagged_object.status = status
        flagged_object.notes = notes
        flagged_object.save()


def get_object_by_title(model, title, manager=None):
    try:
        obj = (manager or model.objects).get(title=title)
    except (model.DoesNotExist, getattr(model, "MultipleObjectsReturned", Exception)) as exc:
        capture_exception(exc)
    else:
        return obj


def update_question_fields_from_classification(question, result, sumo_bot):
    product_result = result.get("product_result", {})
    topic_result = result.get("topic_result", {})
    new_product_title = product_result.get("product")
    new_topic_title = topic_result.get("topic")

    update_fields = {}

    if new_product_title and question.product.title != new_product_title:

        if new_product := get_object_by_title(
            Product,
            new_product_title,
            manager=Product.active,
        ):
            update_fields["product"] = new_product

    if new_topic_title and (
        topic := get_object_by_title(
            Topic,
            new_topic_title,
            manager=Topic.active,
        )
    ):
        update_fields["topic"] = topic

    if update_fields:
        for field, value in update_fields.items():
            setattr(question, field, value)
        question.save()
        question.clear_cached_tags()
        question.tags.clear()
        question.auto_tag()


def process_classification_result(
    question: Question,
    result: dict[str, Any],
) -> None:
    """
    Process the classification result from the LLM and take moderation action.
    Handles spam, flag review, and updates to product and topic if suggested by the classifier.
    """
    sumo_bot = Profile.get_sumo_bot()
    action = result.get("action")
    flag_kwargs = {
        "by_user": sumo_bot,
        "notes": "",
        "question": question,
    }

    match action:
        case ModerationAction.SPAM:
            flag_kwargs.update(
                {
                    "notes": (
                        f"LLM classified as spam, for the following reason:\n"
                        f"{result.get('spam_result', {}).get('reason', '')}"
                    ),
                }
            )
            question.mark_as_spam(sumo_bot)
        case ModerationAction.FLAG_REVIEW:
            flag_kwargs.update(
                {
                    "status": FlaggedObject.FLAG_PENDING,
                    "notes": (
                        f"LLM flagged for manual review, for the following reason:\n"
                        f"{result.get('spam_result', {}).get('reason', '')}"
                    ),
                }
            )
        case _:
            flag_kwargs.update(
                {
                    "reason": FlaggedObject.REASON_CONTENT_MODERATION,
                    "notes": (
                        f"LLM classified as {result.get('topic_result', {}).get('topic', '')}, "
                        f"for the following reason:\n"
                        f"{result.get('topic_result', {}).get('reason', '')}"
                    ),
                }
            )
            update_question_fields_from_classification(question, result, sumo_bot)

    flag_question(**flag_kwargs)
