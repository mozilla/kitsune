import re

import django
from django.conf import settings
from jinja2.ext import babel_extract


EXTRACTION_REGEX = re.compile(
    r"""(?P<funcname>_|N_|gettext|ugettext)\(\s*(?P<quote>['"`])(?P<msgid>.*?)(?P=quote)\s*\)""",
    re.DOTALL,
)


def generate_option(value):
    """
    Generate option to pass to babel_extract() from a TEMPLATES['OPTION'] value
    setting.

    babel_extract() options are meant to be coming from babel config files, so
    everything is based on strings.
    """
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, tuple)):
        return ",".join(value)
    return value


def extract_svelte(fileobj, keywords, comment_tags, options):
    """
    Regular-expression-based extractor for Svelte files.
    """
    text = fileobj.read().decode(options.get("encoding", "utf-8"))

    lineno = 1
    previous_pos = 0
    for match_object in EXTRACTION_REGEX.finditer(text):
        lineno = text.count("\n", previous_pos, match_object.start()) + lineno
        yield (lineno, match_object["funcname"], match_object["msgid"], [])
        previous_pos = match_object.start()


def extract_jinja(fileobj, keywords, comment_tags, options):
    """
    Wrapper around jinja2's babel_extract() that sets the relevant options by
    looking at our django settings.

    This is necessary because jinja2's babel_extract() loads a default
    environment which doesn't have our extensions and doesn't set
    the options we need for trimming, so it can't process all our
    templates and generates a po file that doesn't correspond to our
    gettext calls because of the whitespace differences.
    """

    # It looks like this call is required to make sure jinja2 extensions load properly.
    django.setup()

    # Get the options settings for the Jinja2 templates.
    jinja2_options = {}
    for template in settings.TEMPLATES:
        if template.get("NAME") == "jinja2":
            jinja2_options = template.get("OPTIONS", {})
            break

    options.update(
        {
            name: generate_option(jinja2_options[name])
            for name in [
                "extensions",
                "block_start_string",
                "block_end_string",
                "variable_start_string",
                "variable_end_string",
                "comment_start_string",
                "comment_end_string",
                "line_statement_prefix",
                "line_comment_prefix",
                "trim_blocks",
                "lstrip_blocks",
                "keep_trailing_newline",
            ]
            if name in jinja2_options
        }
    )

    options["trimmed"] = generate_option(
        jinja2_options.get("policies", {}).get("ext.i18n.trimmed", False)
    )

    return babel_extract(fileobj, keywords, comment_tags, options)
