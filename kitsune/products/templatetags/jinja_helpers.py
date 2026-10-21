from django.utils.translation import pgettext
from django_jinja import library
from markupsafe import escape


@library.global_function
def display_curated_message(message):
    """Return the localized callout message as escaped text.

    Django's pgettext is used because the Jinja newstyle one %-formats its result.
    """
    return escape(pgettext("DB: products.CuratedBlock.message", str(message)))
