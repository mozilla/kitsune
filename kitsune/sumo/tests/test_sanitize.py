import markupsafe

from kitsune.sumo.sanitize import (
    RESTRICTED_HTML_ATTRIBUTES,
    RESTRICTED_HTML_TAGS,
    linkify,
)
from kitsune.sumo.templatetags.jinja_helpers import sanitize_external_html
from kitsune.sumo.tests import TestCase


class RestrictedHtmlConstantsTests(TestCase):
    def test_tags_contains_br_and_pre(self):
        self.assertIn("br", RESTRICTED_HTML_TAGS)
        self.assertIn("pre", RESTRICTED_HTML_TAGS)

    def test_tags_contains_headings(self):
        for tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.assertIn(tag, RESTRICTED_HTML_TAGS)

    def test_tags_contains_table_structure(self):
        for tag in ("table", "thead", "tbody", "tfoot", "tr", "td", "th"):
            self.assertIn(tag, RESTRICTED_HTML_TAGS)

    def test_rename_preserves_existing_attribute_entries(self):
        self.assertIn("a", RESTRICTED_HTML_ATTRIBUTES)
        self.assertIn("abbr", RESTRICTED_HTML_ATTRIBUTES)
        self.assertIn("acronym", RESTRICTED_HTML_ATTRIBUTES)


class LinkifyTests(TestCase):
    def test_wraps_bare_url(self):
        self.assertEqual(
            '<a href="https://example.com">https://example.com</a>',
            linkify("https://example.com"),
        )

    def test_nofollow(self):
        self.assertIn('rel="nofollow"', linkify("https://example.com", nofollow=True))

    def test_preserves_existing_html(self):
        self.assertEqual("<p>hello</p>", linkify("<p>hello</p>"))

    def test_malformed_attr_backslash_does_not_raise(self):
        # Regression: justhtml >=1.15.0 refuses to serialize attribute names
        # containing characters like `\`. The tokenizer produces such names
        # when input like `<iframe/src \/\/onload=prompt(1)` lands inside
        # a block context (wikimarkup wraps user text in `<p>` before calling
        # linkify). linkify must drop those attrs before the serializer sees
        # them.
        linkify(r"<p><iframe/src \/\/onload = prompt(1)</p>")

    def test_malformed_attr_lt_does_not_raise(self):
        # Regression: the stray `<` from `</img>` becomes an attribute name.
        linkify("<img src=https://example.com/x.jpg </img>")

    def test_malformed_tag_dot_does_not_raise(self):
        # Regression: a `.` in a tag name (e.g. `<test.test`) is produced
        # by the tokenizer but rejected by the serializer. The element
        # must be unwrapped so its text content survives.
        linkify("<test.test")

    def test_malformed_tag_paren_does_not_raise(self):
        # Regression: a `)` in a tag name (e.g. text like `<mexico)`
        # embedded in a forum post) is tokenized as `<mexico)` and
        # rejected by the serializer.
        linkify("<mexico)")

    def test_malformed_tag_comma_does_not_raise(self):
        # Regression: crash-report-style text containing
        # `<nstarray_copyelements,` produces a tag name ending in `,`
        # that the serializer rejects.
        linkify("<nstarray_copyelements, nsfontfacerulecontainer>content")

    def test_malformed_tag_from_js_bookmarklet_does_not_raise(self):
        # Regression: a `javascript:` bookmarklet pasted as text contains
        # fragments like `i<df.length` that the tokenizer treats as the
        # start of element `<df.length`, producing an unserializable tag.
        linkify("javascript:(function(){for(i=0;i<df.length;++i){}})()")

    def test_malformed_tag_from_binary_payload_does_not_raise(self):
        # Regression: raw binary content (e.g. a ZIP header) contains
        # bytes that the tokenizer interprets as weird tag names. The
        # sanitizer must not raise when any such content is pasted.
        linkify("PK\x03\x04<\x14\x06\b!\x1a text body after binary")

    def test_unwrapped_tag_preserves_inner_text(self):
        # When a tag is unwrapped for being unserializable, its inner
        # text content must survive in the output.
        result = linkify("<foo.bar>hello world</foo.bar>")
        self.assertIn("hello world", result)


class SanitizeExternalHtmlFilterTests(TestCase):
    def test_script_tag_is_stripped(self):
        result = sanitize_external_html("<script>alert(1)</script>")
        self.assertNotIn("<script>", result)

    def test_bold_tag_is_preserved(self):
        result = sanitize_external_html("<b>bold</b>")
        self.assertIn("<b>bold</b>", result)

    def test_anchor_with_href_is_preserved(self):
        result = sanitize_external_html('<a href="https://example.com">link</a>')
        self.assertIn('href="https://example.com"', result)
        self.assertIn("link", result)

    def test_heading_tag_is_preserved(self):
        result = sanitize_external_html("<h2>Section</h2>")
        self.assertIn("<h2>Section</h2>", result)

    def test_table_structure_is_preserved(self):
        result = sanitize_external_html(
            "<table><thead><tr><th>A</th></tr></thead>"
            "<tbody><tr><td>1</td></tr></tbody></table>"
        )
        for fragment in ("<table>", "<thead>", "<tr>", "<th>A</th>", "<tbody>", "<td>1</td>"):
            self.assertIn(fragment, result)

    def test_table_cell_span_attributes_are_preserved(self):
        result = sanitize_external_html(
            '<table><tr><td colspan="2" rowspan="3">x</td></tr></table>'
        )
        self.assertIn('colspan="2"', result)
        self.assertIn('rowspan="3"', result)

    def test_empty_string_returns_empty_string(self):
        self.assertEqual("", sanitize_external_html(""))

    def test_none_returns_empty_string(self):
        self.assertEqual("", sanitize_external_html(None))

    def test_return_value_is_markup_for_nonempty_input(self):
        result = sanitize_external_html("<b>bold</b>")
        self.assertIsInstance(result, markupsafe.Markup)
