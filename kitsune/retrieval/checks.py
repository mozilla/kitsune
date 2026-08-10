"""Validate retrieval task safety and interactive-query settings.

Nothing renews a retrieval lease in the background, so safety rests on a task being unable to
outlive one:

    provider request deadline < task soft limit < task hard limit < lease ttl

Each step earns its place. A request that can outlast the soft limit means the wind-down never
runs. A soft limit at or past the hard limit leaves no room to wind down at all. A hard limit at
or past the lease ttl is the failure this exists to prevent: the lease lapses while the worker
is still writing, and a second worker can pick the document up.

The same function backs a Django system check and ``RetrievalConfig.ready()``, because
``manage.py check`` runs on deploy but a Celery worker start-up does not necessarily run system
checks — and the worker is where it matters.
"""

import math
from itertools import pairwise

from django.conf import settings
from django.core.checks import Error, register

from kitsune.retrieval.embeddings import MIN_EMBEDDING_TIMEOUT_SECONDS


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
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(value)
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
    """Describe invalid independent query timeout/cache settings."""
    problems: list[str] = []
    timeout = settings.RETRIEVAL_QUERY_EMBEDDING_TIMEOUT_SECONDS
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int | float)
        or not math.isfinite(timeout)
        or timeout < MIN_EMBEDDING_TIMEOUT_SECONDS
    ):
        problems.append(
            "RETRIEVAL_QUERY_EMBEDDING_TIMEOUT_SECONDS must be a finite number of seconds "
            f"of at least {MIN_EMBEDDING_TIMEOUT_SECONDS}"
        )

    ttl = settings.RETRIEVAL_QUERY_VECTOR_CACHE_TTL_SECONDS
    if not isinstance(ttl, int) or isinstance(ttl, bool) or ttl <= 0:
        problems.append("RETRIEVAL_QUERY_VECTOR_CACHE_TTL_SECONDS must be a positive integer")
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
