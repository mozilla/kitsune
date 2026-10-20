from parameterized import parameterized

from kitsune.sumo.tests import TestCase
from kitsune.wiki.templatetags.jinja_helpers import scrollable_tables


class ScrollableTablesTests(TestCase):
    @parameterized.expand(
        [
            ("no_table", "<p>Text</p>", "<p>Text</p>"),
            (
                "one_table",
                "<p>a</p><table><tr><td>1</td></tr></table><p>b</p>",
                '<p>a</p><div class="table-scroll"><table><tr><td>1</td></tr></table></div><p>b</p>',
            ),
            (
                "several_tables",
                "<table><tr><td>1</td></tr></table>\n<table><tr><td>2</td></tr></table>",
                '<div class="table-scroll"><table><tr><td>1</td></tr></table></div>\n'
                '<div class="table-scroll"><table><tr><td>2</td></tr></table></div>',
            ),
            (
                "uppercase_with_attributes",
                '<TABLE class="wikitable" style="width:100%"><TR><TD>1</TD></TR></TABLE >',
                '<div class="table-scroll"><TABLE class="wikitable" style="width:100%">'
                "<TR><TD>1</TD></TR></TABLE ></div>",
            ),
            (
                "nested_table",
                "<table><tr><td><table><tr><td>1</td></tr></table></td></tr></table>",
                '<div class="table-scroll"><table><tr><td><table><tr><td>1</td></tr></table>'
                "</td></tr></table></div>",
            ),
            ("unclosed_table", "<table><tr><td>1", "<table><tr><td>1"),
        ]
    )
    def test_wraps_top_level_tables(self, _name, html, expected):
        self.assertEqual(scrollable_tables(html), expected)
