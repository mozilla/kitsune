from django_jinja import library
from markupsafe import Markup

from kitsune.sumo import parser
from kitsune.wiki.diff import BetterHtmlDiff
from kitsune.wiki.facets import documents_for


@library.global_function
def diff_table(content_from, content_to):
    """Creates an HTML diff of the passed in content_from and content_to."""
    html_diff = BetterHtmlDiff()
    diff = html_diff.make_table(content_from.splitlines(), content_to.splitlines(), context=True)
    return Markup(diff)


@library.global_function
def generate_video(v):
    return Markup(parser.generate_video(v))


@library.global_function
def kb_documents_for(user, locale, topics=None, products=None, current_document=None):
    return documents_for(user, locale, topics, products, current_document)
