"""Validate retrieval task safety and interactive-query settings.

Nothing renews a retrieval lease in the background, so safety rests on a task being unable to
outlive one:

    provider request deadline < task soft limit < task hard limit < lease ttl

Backs both the Django system check and ``RetrievalConfig.ready()``, because a Celery worker
start-up does not necessarily run system checks — and the worker is where it matters.
"""

import re
from itertools import pairwise

from django.conf import settings
from django.core.checks import Error, register

from kitsune.retrieval.embeddings import MIN_EMBEDDING_TIMEOUT_SECONDS
from kitsune.retrieval.fingerprints import is_valid_similarity_floor
from kitsune.retrieval.index import SIMILARITY
from kitsune.retrieval.validation import is_finite_number, is_positive_int

_SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")
_RATE = re.compile(r"(?:0|[1-9][0-9]*)/(?:[1-9][0-9]*)?[smhd]\Z")


def is_valid_query_embedding_rate(value: object) -> bool:
    """Return whether value is a supported Django Ratelimit rate."""
    return isinstance(value, str) and _RATE.fullmatch(value) is not None


def task_timing_problems() -> list[str]:
    """Describe invalid limits and ordering violations."""
    ordered = (
        ("RETRIEVAL_EMBEDDING_TIMEOUT_SECONDS", settings.RETRIEVAL_EMBEDDING_TIMEOUT_SECONDS),
        (
            "RETRIEVAL_TASK_SOFT_TIME_LIMIT_SECONDS",
            settings.RETRIEVAL_TASK_SOFT_TIME_LIMIT_SECONDS,
        ),
        ("RETRIEVAL_TASK_TIME_LIMIT_SECONDS", settings.RETRIEVAL_TASK_TIME_LIMIT_SECONDS),
        ("RETRIEVAL_LOCK_TTL_SECONDS", settings.RETRIEVAL_LOCK_TTL_SECONDS),
    )
    problems: list[str] = []
    valid_names: set[str] = set()
    for name, value in ordered:
        is_embedding_timeout = name == "RETRIEVAL_EMBEDDING_TIMEOUT_SECONDS"
        if (
            not is_finite_number(value)
            or value <= 0
            or (is_embedding_timeout and value < MIN_EMBEDDING_TIMEOUT_SECONDS)
        ):
            qualifier = (
                f"at least {MIN_EMBEDDING_TIMEOUT_SECONDS}" if is_embedding_timeout else "positive"
            )
            problems.append(f"{name} must be a finite {qualifier} number of seconds")
        else:
            valid_names.add(name)

    for (lower_name, lower), (upper_name, upper) in pairwise(ordered):
        if lower_name in valid_names and upper_name in valid_names and lower >= upper:
            problems.append(f"{lower_name} ({lower}) must be less than {upper_name} ({upper})")
    return problems


def query_configuration_problems() -> list[str]:
    """Describe invalid interactive-query settings and bounded retrieval work."""
    problems: list[str] = []
    timeout = settings.RETRIEVAL_QUERY_EMBEDDING_TIMEOUT_SECONDS
    if not is_finite_number(timeout) or timeout < MIN_EMBEDDING_TIMEOUT_SECONDS:
        problems.append(
            "RETRIEVAL_QUERY_EMBEDDING_TIMEOUT_SECONDS must be a finite number of seconds "
            f"of at least {MIN_EMBEDDING_TIMEOUT_SECONDS}"
        )

    ttl = settings.RETRIEVAL_QUERY_VECTOR_CACHE_TTL_SECONDS
    if not is_positive_int(ttl):
        problems.append("RETRIEVAL_QUERY_VECTOR_CACHE_TTL_SECONDS must be a positive integer")

    bounds = (
        ("RETRIEVAL_SEMANTIC_K", settings.RETRIEVAL_SEMANTIC_K),
        ("RETRIEVAL_KNN_NUM_CANDIDATES", settings.RETRIEVAL_KNN_NUM_CANDIDATES),
        ("RETRIEVAL_RRF_RANK_WINDOW_SIZE", settings.RETRIEVAL_RRF_RANK_WINDOW_SIZE),
    )
    valid_bounds = set()
    for name, value in bounds:
        if not is_positive_int(value):
            problems.append(f"{name} must be a positive integer")
        else:
            valid_bounds.add(name)
    if (
        "RETRIEVAL_SEMANTIC_K" in valid_bounds
        and "RETRIEVAL_KNN_NUM_CANDIDATES" in valid_bounds
        and settings.RETRIEVAL_KNN_NUM_CANDIDATES < settings.RETRIEVAL_SEMANTIC_K
    ):
        problems.append("RETRIEVAL_KNN_NUM_CANDIDATES must be at least RETRIEVAL_SEMANTIC_K")

    segment_size = settings.RETRIEVAL_SEARCH_SEGMENT_SIZE
    if not is_positive_int(segment_size):
        problems.append("RETRIEVAL_SEARCH_SEGMENT_SIZE must be a positive integer")
    elif (
        "RETRIEVAL_RRF_RANK_WINDOW_SIZE" in valid_bounds
        and segment_size + 1 > settings.RETRIEVAL_RRF_RANK_WINDOW_SIZE
    ):
        problems.append(
            "RETRIEVAL_SEARCH_SEGMENT_SIZE and the has-more probe must fit within "
            "RETRIEVAL_RRF_RANK_WINDOW_SIZE"
        )

    session_ttl = settings.RETRIEVAL_SEARCH_SESSION_TTL_SECONDS
    if not is_positive_int(session_ttl):
        problems.append("RETRIEVAL_SEARCH_SESSION_TTL_SECONDS must be a positive integer")

    if settings.RETRIEVAL_LEXICAL_DEFAULT_OPERATOR not in ("AND", "OR"):
        problems.append("RETRIEVAL_LEXICAL_DEFAULT_OPERATOR must be AND or OR")
    if not settings.RETRIEVAL_LEXICAL_MINIMUM_SHOULD_MATCH:
        problems.append("RETRIEVAL_LEXICAL_MINIMUM_SHOULD_MATCH must not be empty")
    if settings.RETRIEVAL_LOCALE_COMPOSITION not in ("combined", "separate"):
        problems.append("RETRIEVAL_LOCALE_COMPOSITION must be combined or separate")
    if not is_valid_query_embedding_rate(settings.RETRIEVAL_QUERY_EMBEDDING_RATE):
        problems.append(
            "RETRIEVAL_QUERY_EMBEDDING_RATE must use count/[duration]unit, such as 10/m"
        )

    floors = settings.RETRIEVAL_KNN_SIMILARITY_FLOORS
    if not isinstance(floors, dict):
        problems.append("RETRIEVAL_KNN_SIMILARITY_FLOORS must be an object")
    else:
        for fingerprint, floor in floors.items():
            if not isinstance(fingerprint, str) or not _SHA256_HEX.fullmatch(fingerprint):
                problems.append(
                    "RETRIEVAL_KNN_SIMILARITY_FLOORS keys must be SHA-256 fingerprints"
                )
            if not is_valid_similarity_floor(floor, SIMILARITY):
                problems.append(
                    "RETRIEVAL_KNN_SIMILARITY_FLOORS values must be cosine similarities "
                    "between -1 and 1"
                )
    return problems


@register()
def check_retrieval_task_timing(app_configs, **kwargs):
    return [
        Error(problem, id="retrieval.E001", hint="See kitsune/retrieval/checks.py.")
        for problem in task_timing_problems()
    ]


@register()
def check_retrieval_query_configuration(app_configs, **kwargs):
    return [
        Error(problem, id="retrieval.E002", hint="See kitsune/retrieval/checks.py.")
        for problem in query_configuration_problems()
    ]
