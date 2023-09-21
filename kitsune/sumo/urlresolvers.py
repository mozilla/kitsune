import contextlib

from django.urls import reverse as django_reverse
from django.utils.translation import override


def reverse(viewname, urlconf=None, args=None, kwargs=None, current_app=None, locale=None):
    """
    Thin wrapper around Django's reverse that allows you to force the locale to something
    other than the currently activated locale.
    """
    with override(locale) if locale else contextlib.nullcontext():
        return django_reverse(
            viewname, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app
        )
