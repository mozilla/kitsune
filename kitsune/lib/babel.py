from io import BytesIO

from babel.messages.extract import extract_javascript
import django
from django.conf import settings
from jinja2.ext import babel_extract


SVELTE_SPECIAL_TAG_PREFIXES = set([b"{#", b"{:", b"{/", b"{@"])


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
    Custom extractor for Svelte files.

    Since Babel's built-in JavaScript extractor is designed to handle JSX
    files as well plain JavaScript files, it can also handle nearly all of
    the syntax within a Svelte file. What it doesn't always handle well are
    the statements that open, continue, and close Svelte logic blocks. They
    sometimes confuse it such that it fails to recognize some localizable
    strings. This custom extractor essentially hides those statements from
    the underlying Babel JavaScript extractor, while maintaining the same
    line numbers as the original Svelte file.

    NOTE: This approach assumes that any special Svelte tags always exist
          on their own line without anything else on that line. Of course,
          this approach is not as elegant as using a full-blown parser for
          Svelte files, but it's much easier and will work for our current
          practical purposes.
    """
    filtered = BytesIO()
    for line in fileobj:
        if line.lstrip()[:2] in SVELTE_SPECIAL_TAG_PREFIXES:
            # Write a new line to maintain equivalent line numbers.
            filtered.write(b"\n")
        else:
            filtered.write(line)
    filtered.seek(0)
    return extract_javascript(filtered, keywords, comment_tags, options)


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
