"""System checks for site-wide settings.

Add further checks below, each with its own registered function.
"""

from django.conf import settings
from django.core.checks import Error, register

NUL_STRIPPING_MIDDLEWARE = "kitsune.sumo.middleware.StripNulCharactersMiddleware"


def nul_stripping_middleware_problems() -> list[str]:
    """Check that NUL stripping always runs first.

    Reading request.GET caches its parse of QUERY_STRING, so whichever middleware
    reads it first decides what every later one sees. StripNulCharactersMiddleware
    works by cleaning QUERY_STRING before anything else reads request.GET.
    """
    if not settings.MIDDLEWARE or settings.MIDDLEWARE[0] != NUL_STRIPPING_MIDDLEWARE:
        return [f"{NUL_STRIPPING_MIDDLEWARE} must be the first entry in MIDDLEWARE"]
    return []


@register()
def check_nul_stripping_middleware(app_configs, **kwargs):
    return [
        Error(problem, id="sumo.E001", hint="See kitsune/sumo/checks.py.")
        for problem in nul_stripping_middleware_problems()
    ]
