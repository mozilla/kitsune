import re

from django_jinja import library
from markupsafe import Markup

from kitsune.wiki.content_managers import HybridContentManager
from kitsune.wiki.diff import BetterHtmlDiff
from kitsune.wiki.facets import documents_for
from kitsune.wiki.models import Document

TABLE_TAG = re.compile(r"<table(?=[\s/>])|</table\s*>", re.IGNORECASE)


@library.global_function
def diff_table(content_from, content_to):
    """Creates an HTML diff of the passed in content_from and content_to."""
    html_diff = BetterHtmlDiff()
    diff = html_diff.make_table(content_from.splitlines(), content_to.splitlines(), context=True)
    return Markup(diff)


@library.global_function
def kb_documents_for(user, locale, topics=None, products=None, current_document=None):
    return documents_for(user, locale, topics, products, current_document)


@library.global_function
def is_auto_published_translation(doc: Document) -> bool:
    """
    Convenience function that returns a boolean indicating whether or not
    the given document's current revision was machine-generated and not
    reviewed by a human.
    """
    return HybridContentManager().is_auto_published_translation(doc.current_revision)


@library.filter
def scrollable_tables(html):
    """Wrap each top-level table in a horizontal scroll container."""
    if not isinstance(html, str) or not TABLE_TAG.search(html):
        return html

    parts = []
    depth = 0
    cursor = 0
    for match in TABLE_TAG.finditer(html):
        if match.group().startswith("</"):
            if depth == 0:
                continue
            depth -= 1
            if depth == 0:
                parts += [html[cursor : match.end()], "</div>"]
                cursor = match.end()
        else:
            if depth == 0:
                parts += [html[cursor : match.start()], '<div class="table-scroll">']
                cursor = match.start()
            depth += 1

    # Leave malformed markup with an unclosed table as it is.
    if depth:
        return html
    parts.append(html[cursor:])
    return "".join(parts)
