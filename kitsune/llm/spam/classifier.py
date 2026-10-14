from typing import Any, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from kitsune.llm.prompt import model_to_dict
from kitsune.llm.spam.prompt import (
    build_spam_assessment_prompt,
    build_spam_input,
    build_spam_questions,
    spam_assessment_parser,
)
from kitsune.llm.utils import (
    DecisionError,
    evaluate_decisions,
    get_llm,
    get_probability_setting,
    parse_probability,
)


class ModerationAction(models.TextChoices):
    NOT_SPAM = "not_spam", _lazy("Not Spam")
    SPAM = "spam", _lazy("Spam")
    FLAG_REVIEW = "flag_review", _lazy("Flag for Review")


def determine_action_from_spam_result(spam_result: dict[str, Any]) -> ModerationAction:
    """Apply configured probability cutoffs; incomplete decisions always require review."""
    review = get_probability_setting("SPAM_REVIEW_PROBABILITY")
    reject = get_probability_setting("SPAM_REJECT_PROBABILITY")
    relevance_review = get_probability_setting("SPAM_RELEVANCE_REVIEW_PROBABILITY")
    if review >= reject:
        raise ImproperlyConfigured(
            "SPAM_REVIEW_PROBABILITY must be less than SPAM_REJECT_PROBABILITY."
        )
    probability = parse_probability(spam_result.get("probability"))
    relevance_uncertainty = parse_probability(spam_result.get("relevance_uncertainty_probability"))
    if probability is None or relevance_uncertainty is None:
        action = ModerationAction.FLAG_REVIEW
    elif probability < review:
        action = ModerationAction.NOT_SPAM
    elif probability >= reject and relevance_uncertainty < relevance_review:
        action = ModerationAction.SPAM
    else:
        action = ModerationAction.FLAG_REVIEW
    return cast(ModerationAction, action)


def _decision_probability(answers: Any, name: str, label: str) -> tuple[float | None, str]:
    answer = answers.get(name) if isinstance(answers, dict) else None
    match answer:
        case {"type": "refusal"}:
            return None, _("{label} decision was refused.").format(label=label)
        case {"type": "predicate", "name": answer_name, "probability": value} if (
            answer_name == name
        ):
            probability = parse_probability(value)
            if probability is None:
                return None, _("{label} decision did not supply a valid probability.").format(
                    label=label
                )
            return probability, ""
        case dict():
            return None, _("{label} decision is malformed.").format(label=label)
        case _:
            return None, _("{label} decision is missing or malformed.").format(label=label)


def classify_spam(payload: dict[str, Any]) -> dict[str, Any]:
    """Screen Mozilla-wide spam without using the selected product or topic."""
    questions = build_spam_questions(payload["channel"])
    input_text = build_spam_input(payload)
    try:
        answers = evaluate_decisions(input_text, questions)
    except DecisionError:
        return {
            "spam_result": {
                "probability": None,
                "relevance_uncertainty_probability": None,
                "reason": _("Spam classification unavailable; manual review required."),
            }
        }

    probability, spam_reason = _decision_probability(answers, "spam", _("Spam"))
    relevance_uncertainty, relevance_reason = _decision_probability(
        answers, "relevance_uncertainty", _("Relevance-only uncertainty")
    )
    return {
        "spam_result": {
            "probability": probability,
            "relevance_uncertainty_probability": relevance_uncertainty,
            "reason": " ".join(reason for reason in (spam_reason, relevance_reason) if reason),
        }
    }


def assess_spam(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an independent advisory assessment; provider and parsing errors propagate."""
    prompt = build_spam_assessment_prompt(payload["channel"])
    llm = get_llm(model_name=settings.SPAM_ASSESSMENT_MODEL, temperature=0.0)
    chain = prompt | llm | spam_assessment_parser | model_to_dict
    return chain.invoke({"input_text": build_spam_input(payload)})
