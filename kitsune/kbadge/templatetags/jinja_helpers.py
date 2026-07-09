from django.utils.translation import pgettext
from django_jinja import library
from markupsafe import escape


def _display_db_string(value, context):
    """Return a localized DB string, HTML-escaped for safe rendering.

    Badge titles and descriptions are plain-text labels, but they're localized
    via pgettext, whose newstyle return value is marked safe (Markup) under
    autoescape. That bypasses Jinja's autoescaping, so a value containing markup
    would render unescaped. Escaping the translated value here treats it as the
    plain text it is, keeping it safe in both element-text and quoted-attribute
    contexts.
    """
    return escape(pgettext(context, str(value)))


@library.global_function
def display_badge_title(title):
    return _display_db_string(title, "DB: kbadge.Badge.title")


@library.global_function
def display_badge_description(description):
    return _display_db_string(description, "DB: kbadge.Badge.description")
