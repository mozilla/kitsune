from jingo import register
import jinja2

from sumo import parser
from wiki.diff import BetterHtmlDiff


@register.function
def diff_table(content_from, content_to):
    """Creates an HTML diff of the passed in content_from and content_to."""
    html_diff = BetterHtmlDiff()
    diff = html_diff.make_table(content_from.splitlines(),
                                content_to.splitlines(), context=True)
    return jinja2.Markup(diff)


@register.function
def generate_video(v):
    return jinja2.Markup(parser.generate_video(v))
