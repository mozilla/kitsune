import re
from unittest.mock import patch

from django.conf import settings
from parameterized import parameterized
from pyquery import PyQuery as pq

import kitsune.sumo.tests.test_parser
from kitsune.gallery.tests import ImageFactory, TemporaryMediaRoots
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory
from kitsune.wiki.config import TEMPLATE_TITLE_PREFIX, TEMPLATES_CATEGORY
from kitsune.wiki.models import Audience, Document
from kitsune.wiki.parser import PATTERNS, RECURSION_MESSAGE, ForParser, WikiParser, _key_split
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    AudienceFactory,
    DocumentFactory,
    RevisionFactory,
    TemplateDocumentFactory,
)


def doc_rev_parser(*args, **kwargs):
    return kitsune.sumo.tests.test_parser.doc_rev_parser(*args, parser_cls=WikiParser, **kwargs)


def doc_parse_markup(content, markup):
    """Create a doc with given content and parse given markup."""
    _, _, p = doc_rev_parser(content, TEMPLATE_TITLE_PREFIX + "test", category=TEMPLATES_CATEGORY)
    doc = pq(p.parse(markup))
    return (doc, p)


class SimpleSyntaxTestCase(TestCase):
    """Simple syntax regexing, like {note}...{/note}, {key Ctrl+K}"""

    def test_block_and_inline_syntax(self):
        """{note}, {warning} and the custom inline tags wrap their content."""
        cases = [
            ("{note}this is a note{/note}", "div.note", "this is a note"),
            ("{warning}this is a warning{/warning}", "div.warning", "this is a warning"),
            ("{warning}\nthis is a warning\n{/warning}", "div.warning", "this is a warning"),
            (
                "\n\n{warning}\n\nthis is a warning\n\n{/warning}\n\n",
                "div.warning",
                "this is a warning",
            ),
            *(
                (f"{{{tag} this is a {tag}}}", f"span.{tag}", f"this is a {tag}")
                for tag in ("menu", "button", "filepath", "pref")
            ),
        ]
        for markup, selector, text in cases:
            with self.subTest(markup=markup):
                self.assertEqual(text, pq(WikiParser().parse(markup))(selector).text())

    def test_general_warning_note(self):
        """A bunch of wiki text with {warning} and {note}"""
        p = WikiParser()
        doc = pq(
            p.parse(
                "\n\n{warning}\n\nthis is a warning\n\n{note}"
                "this is a note{warning}!{/warning}{/note}"
                "[[Installing Firefox]] '''internal''' ''link''"
                "{/warning}\n\n"
            )
        )
        self.assertEqual("!", doc("div.warning div.warning").text())
        self.assertEqual("this is a note\n!", doc("div.note").text())
        self.assertEqual("Installing Firefox", doc("a").text())
        self.assertEqual("internal", doc("strong").text())
        self.assertEqual("link", doc("em").text())

    def test_key_inline(self):
        """{key} stays inline"""
        p = WikiParser()
        doc = pq(p.parse("{key Cmd+Shift+Q}"))
        self.assertEqual(1, len(doc("p")))
        self.assertEqual(
            '<span class="key">Cmd</span> + <span class="key">Shift</span>'
            ' + <span class="key">Q</span>',
            doc.html().replace("\n", ""),
        )

    def test_template_inline(self):
        """Inline templates are not wrapped in <p>s"""
        doc, _p = doc_parse_markup(
            '<span class="key">{{{1}}}</span>', "[[T:test|Cmd]] + [[T:test|Shift]]"
        )
        self.assertEqual(1, len(doc("p")))

    def test_template_multiline(self):
        """Multiline templates are wrapped in <p>s"""
        doc, _p = doc_parse_markup('<span class="key">\n{{{1}}}</span>', "[[T:test|Cmd]]")
        self.assertEqual(3, len(doc("p")))

    def test_key_split_callback(self):
        """The _key_split regex callback does what it claims"""
        key_p = PATTERNS[2][0]
        # Multiple keys, with spaces
        self.assertEqual(
            '<span class="key">ctrl</span> + <span class="key">alt</span> + '
            '<span class="key">del</span>',
            key_p.sub(_key_split, "{key ctrl + alt +   del}"),
        )
        # Single key with spaces in it
        self.assertEqual('<span class="key">a key</span>', key_p.sub(_key_split, "{key a key}"))
        # Multiple keys with quotes and spaces
        self.assertEqual(
            '<span class="key">"Param-One" and</span> + <span class="key">'
            'param</span> + <span class="key">two</span>',
            key_p.sub(_key_split, '{key  "Param-One" and + param+two}'),
        )
        self.assertEqual(
            '<span class="key">multi\nline</span> + <span class="key">me</span>',
            key_p.sub(_key_split, "{key multi\nline\n+me}"),
        )

    def test_key_split_brace_callback(self):
        """Adding brace inside {key ...}"""
        key_p = PATTERNS[2][0]
        self.assertEqual(
            '<span class="key">ctrl</span> + <span class="key">and</span> Here is }',
            key_p.sub(_key_split, "{key ctrl + and} Here is }"),
        )
        self.assertEqual(
            '<span class="key">ctrl</span> + <span class="key">and</span> + '
            '<span class="key">{</span>',
            key_p.sub(_key_split, "{key ctrl + and + {}"),
        )

    def test_general_warning_note_inline_custom(self):
        """A mix of custom inline syntax with warnings and notes"""
        p = WikiParser()
        doc = pq(
            p.parse(
                "\n\n{warning}\n\nthis is a {button warning}\n{note}"
                "this is a {menu note}{warning}!{/warning}{/note}"
                "'''{filepath internal}''' ''{menu hi!}''{/warning}"
            )
        )
        self.assertEqual("warning", doc("div.warning span.button").text())
        self.assertEqual("this is a note\n!", doc("div.note").text())
        self.assertEqual("note", doc("div.warning div.note span.menu").text())
        self.assertEqual("internal", doc("strong span.filepath").text())
        self.assertEqual("hi!", doc("em span.menu").text())

    def test_comments(self):
        """Markup containing taggy comments shouldn't truncate afterward."""
        p = WikiParser()

        # This used to truncate after the comment when rendered:
        self.assertEqual(p.parse("Start <!-- <foo --> End"), "<p>Start  End\n</p>")

        # Just make sure these don't go awry either:
        self.assertEqual(p.parse("Start <!-- <foo> --> End"), "<p>Start  End\n</p>")
        self.assertEqual(p.parse("Start <!-- foo> --> End"), "<p>Start  End\n</p>")

    def test_internal_links(self):
        """Make sure internal links work correctly when not to redirected
        articles and when to redirected articles"""
        p = WikiParser()

        # Create a new article
        rev = ApprovedRevisionFactory()
        doc = rev.document
        doc.current_revision = rev
        doc.title = "Real article"
        doc.save()

        # Change the slug of the article to create a redirected article
        old_slug = doc.slug
        doc.slug = "real-article"
        doc.save()
        redirect = Document.objects.get(slug=old_slug)

        # Both internal links should link to the same article
        self.assertEqual(
            p.parse("[[{}]]".format(doc.title)),
            '<p><a href="/en-US/kb/{}">{}</a>\n</p>'.format(doc.slug, doc.title),
        )
        self.assertEqual(
            p.parse("[[{}]]".format(redirect.title)),
            '<p><a href="/en-US/kb/{}">{}</a>\n</p>'.format(doc.slug, doc.title),
        )


class TestWikiTemplate(TestCase):
    def test_template(self):
        """Simple template markup."""
        doc, _ = doc_parse_markup("Test content", "[[Template:test]]")
        self.assertEqual("Test content", doc.text())

    def test_template_does_not_exist(self):
        """Return a message if template does not exist"""
        p = WikiParser()
        doc = pq(p.parse("[[Template:test]]"))
        self.assertEqual(
            'The template "test" does not exist or has no approved revision.', doc.text()
        )

    def test_template_locale(self):
        """Localized template is returned."""
        py_doc, p = doc_parse_markup("English content", "[[Template:test]]")
        parent = TemplateDocumentFactory()
        d = TemplateDocumentFactory(
            parent=parent, title=TEMPLATE_TITLE_PREFIX + "test", locale="fr"
        )
        ApprovedRevisionFactory(content="French Content", document=d)
        self.assertEqual(py_doc.text(), "English content")
        py_doc = pq(p.parse("[[T:test]]", locale="fr"))
        self.assertEqual(py_doc.text(), "French Content")

    def test_template_not_exist(self):
        """If template does not exist in set locale or English."""
        p = WikiParser()
        doc = pq(p.parse("[[T:test]]", locale="fr"))
        self.assertEqual("Le modèle « test » n’existe pas ou n’a pas été approuvé.", doc.text())

    def test_template_locale_fallback(self):
        """If localized template does not exist, fall back to English."""
        _, p = doc_parse_markup("English content", "[[Template:test]]")
        doc = pq(p.parse("[[T:test]]", locale="fr"))
        self.assertEqual("English content", doc.text())

    def test_template_params(self):
        """Anonymous, named and numbered arguments fill the template's placeholders."""
        for name, content in (
            ("pos", "{{{1}}}:{{{2}}}"),
            ("named", "{{{a}}}:{{{b}}}"),
            ("mixed", "{{{1}}}:{{{hi}}}:{{{3}}}"),
        ):
            doc_rev_parser(content, TEMPLATE_TITLE_PREFIX + name, category=TEMPLATES_CATEGORY)
        for markup, expected in (
            ("[[Template:pos|one|two]]", "one:two"),
            ("[[T:pos|two|one]]", "two:one"),
            ("[[Template:named|a=one|b=two]]", "one:two"),
            ("[[T:named|a=two|b=one]]", "two:one"),
            ("[[Template:pos|2=one|1=two]]", "two:one"),
            ("[[T:pos|2=two|1=one]]", "one:two"),
            ("[[T:mixed|hi=test|a|3=z]]", "a:test:z"),
        ):
            with self.subTest(markup):
                self.assertEqual(expected, pq(WikiParser().parse(markup)).text())

    def test_template_wiki_markup(self):
        """A template with wiki markup"""
        doc, _ = doc_parse_markup(
            "{{{1}}}:{{{2}}}\n''wiki''\n'''markup'''", "[[Template:test|2=one|1=two]]"
        )

        self.assertEqual("two:one", doc("p")[1].text.replace("\n", ""))
        self.assertEqual("wiki", doc("em")[0].text)
        self.assertEqual("markup", doc("strong")[0].text)

    def test_template_args_inline_wiki_markup(self):
        """Args that contain inline wiki markup are parsed"""
        doc, _ = doc_parse_markup("{{{1}}}\n\n{{{2}}}", "[[Template:test|'''one'''|''two'']]")

        self.assertEqual(
            "<p/><p><strong>one</strong></p><p><em>two</em></p><p/>", doc.html().replace("\n", "")
        )

    def test_template_args_block_wiki_markup(self):
        """Args that contain block level wiki markup aren't parsed"""
        doc, _ = doc_parse_markup("{{{1}}}\n\n{{{2}}}", "[[Template:test|* ordered|# list]]")

        self.assertEqual("<p/><p>* ordered</p><p># list</p><p/>", doc.html().replace("\n", ""))

    def test_unapproved_template(self):
        TemplateDocumentFactory(title=TEMPLATE_TITLE_PREFIX + "new")
        p = WikiParser()
        doc = pq(p.parse("[[T:new]]"))
        self.assertEqual(
            'The template "new" does not exist or has no approved revision.', doc.text()
        )

    def test_for_in_template(self):
        """Verify that {for}'s render correctly in template."""
        d = TemplateDocumentFactory(title=TEMPLATE_TITLE_PREFIX + "for")
        ApprovedRevisionFactory(document=d, content="{for win}windows{/for}{for mac}mac{/for}")
        p = WikiParser()
        content = p.parse("[[{}for]]".format(TEMPLATE_TITLE_PREFIX))
        self.assertEqual(
            '<p><span class="for" data-for="win">windows</span>'
            '<span class="for" data-for="mac">mac</span>\n\n</p>',
            content,
        )

    def test_button_for_nesting(self):
        """You can nest {for}s inside {button}."""
        text = "{button start {for mac}mac{/for}{for win}win{/for} rest}"
        p = WikiParser()
        content = p.parse(text)
        self.assertEqual(
            '<p><span class="button">start '
            '<span class="for" data-for="mac">mac</span>'
            '<span class="for" data-for="win">win</span> '
            "rest</span>\n</p>",
            content,
        )

    def test_button_image_for_nesting(self):
        """You can nest [[Image:]] inside {for} inside {button}."""
        ImageFactory(title="image-file.png")
        text = "{button {for mac}[[Image:image-file.png]]{/for} text}"
        p = WikiParser()
        doc = pq(p.parse(text))
        assert "frameless" in doc("img").attr("class")
        self.assertEqual(0, doc("div.caption").length)
        self.assertEqual(0, doc("div.img").length)

    def test_direct_recursion(self):
        """Make sure direct recursion is caught on the very first nesting."""
        d = TemplateDocumentFactory(title=TEMPLATE_TITLE_PREFIX + "Boo")

        # Twice so the second revision sees content identical to itself:
        ApprovedRevisionFactory.create_batch(
            2, document=d, content="Fine [[{}Boo]] Fellows".format(TEMPLATE_TITLE_PREFIX)
        )

        recursion_message = RECURSION_MESSAGE % (TEMPLATE_TITLE_PREFIX + "Boo")
        expected = "<p>Fine {} Fellows\n</p>".format(recursion_message)
        self.assertEqual(expected, d.content_parsed)

    def test_indirect_recursion(self):
        """Make sure indirect recursion is caught."""
        boo = TemplateDocumentFactory(title=TEMPLATE_TITLE_PREFIX + "Boo")
        yah = TemplateDocumentFactory(title=TEMPLATE_TITLE_PREFIX + "Yah")
        ApprovedRevisionFactory(
            document=boo, content="Paper [[{}Yah]] Cups".format(TEMPLATE_TITLE_PREFIX)
        )
        ApprovedRevisionFactory(
            document=yah, content="Wooden [[{}Boo]] Bats".format(TEMPLATE_TITLE_PREFIX)
        )
        recursion_message = RECURSION_MESSAGE % (TEMPLATE_TITLE_PREFIX + "Boo")
        self.assertEqual(
            "<p>Paper Wooden {} Bats\n Cups\n</p>".format(recursion_message), boo.content_parsed
        )


class TestWikiInclude(TestCase):
    def test_revision_include(self):
        """Simple include markup."""
        p = WikiParser()
        _, _, p = doc_rev_parser("Test content", "Test title")

        # Existing title returns document's content
        doc = pq(p.parse("[[I:Test title]]"))
        self.assertEqual("Test content", doc.text())

        # Nonexisting title returns 'Document not found'
        doc = pq(p.parse("[[Include:Another title]]"))
        self.assertEqual('The document "Another title" does not exist.', doc.text())

    def test_revision_include_locale(self):
        """Include finds document in the correct locale."""
        _, _, p = doc_rev_parser("English content", "Test title")
        # Parsing in English should find the French article
        doc = pq(p.parse("[[Include:Test title]]", locale="en-US"))
        self.assertEqual("English content", doc.text())
        # The French article will include the English content as fallback.
        doc = pq(p.parse("[[I:Test title]]", locale="fr"))
        self.assertEqual("English content", doc.text())
        # Create the French article, and test again
        parent_rev = RevisionFactory()
        d = DocumentFactory(parent=parent_rev.document, title="Test title", locale="fr")
        ApprovedRevisionFactory(document=d, content="French content")
        # Parsing in French should find the French article
        doc = pq(p.parse("[[Include:Test title]]", locale="fr"))
        self.assertEqual("French content", doc.text())

    def test_direct_recursion(self):
        """Make sure direct recursion is caught on the very first nesting."""
        d = DocumentFactory(title="Boo")
        # Twice so the second revision sees content identical to itself:
        ApprovedRevisionFactory.create_batch(2, document=d, content="Fine [[Include:Boo]] Fellows")
        self.assertEqual(
            "<p>Fine %s Fellows\n</p>" % (RECURSION_MESSAGE % "Boo"), d.content_parsed
        )

    def test_indirect_recursion(self):
        """Make sure indirect recursion is caught."""
        boo = DocumentFactory(title="Boo")
        yah = DocumentFactory(title="Yah")
        ApprovedRevisionFactory(document=boo, content="Paper [[Include:Yah]] Cups")
        ApprovedRevisionFactory(document=yah, content="Wooden [[Include:Boo]] Bats")
        recursion_message = RECURSION_MESSAGE % "Boo"

        # boo.content_parsed is something like <p>Paper </p><p>Wooden
        # [Recursive inclusion of "Boo"] Bats\n</p> Cups\n<p></p>.
        self.assertEqual(
            "Paper Wooden {} Bats Cups".format(recursion_message),
            re.sub(r"</?p>|\n", "", boo.content_parsed),
        )

    def _make_parser(self, source_doc):
        """Helper to create a WikiParser with the restriction context of a source document."""
        return WikiParser(
            doc_id=source_doc.id,
            audience_ids=source_doc.original.private_audience_ids,
        )

    def test_include_unrestricted_document_from_restricted(self):
        """A restricted doc including an unrestricted doc should work."""
        unrestricted = DocumentFactory(title="Public Doc")
        ApprovedRevisionFactory(document=unrestricted, content="Public content")

        including = DocumentFactory(title="Restricted Source", audiences=[AudienceFactory()])
        ApprovedRevisionFactory(document=including)
        p = self._make_parser(including)
        doc = pq(p.parse("[[Include:Public Doc]]"))
        self.assertEqual("Public content", doc.text())

    def test_include_restricted_document_from_unrestricted(self):
        """
        A public doc, even one with private audiences too, rejects a restricted include,
        and so does a doc with no audiences (Staff only).
        """
        audience = AudienceFactory()
        restricted = DocumentFactory(title="Restricted Doc", audiences=[audience])
        ApprovedRevisionFactory(document=restricted, content="Secret content")

        for source_audiences in (
            [Audience.objects.default()],
            [Audience.objects.default(), audience],
            [],
        ):
            with self.subTest(source_audiences=source_audiences):
                unrestricted = DocumentFactory(audiences=source_audiences)
                ApprovedRevisionFactory(document=unrestricted)
                p = self._make_parser(unrestricted)
                doc = pq(p.parse("[[Include:Restricted Doc]]"))
                self.assertNotIn("Secret content", doc.text())

    def test_include_restricted_document_from_same_audience(self):
        """A restricted doc including another doc with the same audience should work."""
        audience = AudienceFactory()
        restricted = DocumentFactory(title="Restricted Doc", audiences=[audience])
        ApprovedRevisionFactory(document=restricted, content="Secret content")

        including = DocumentFactory(title="Also Restricted", audiences=[audience])
        ApprovedRevisionFactory(document=including)
        p = self._make_parser(including)
        doc = pq(p.parse("[[Include:Restricted Doc]]"))
        self.assertEqual("Secret content", doc.text())

    def test_include_restricted_document_from_subset_audiences(self):
        """A doc whose audiences are a subset of an included doc's audiences should work."""
        audience_a = AudienceFactory()
        audience_b = AudienceFactory()
        restricted = DocumentFactory(title="Restricted Doc", audiences=[audience_a, audience_b])
        ApprovedRevisionFactory(document=restricted, content="Secret content")

        # Every reader of the including doc can also read the included doc.
        including = DocumentFactory(title="Narrower Doc", audiences=[audience_a])
        ApprovedRevisionFactory(document=including)
        p = self._make_parser(including)
        doc = pq(p.parse("[[Include:Restricted Doc]]"))
        self.assertEqual("Secret content", doc.text())

    def test_include_restricted_document_from_non_subset_audiences(self):
        """A doc whose audiences aren't a subset of the included doc's should not work."""
        group = GroupFactory()
        restricted = DocumentFactory(
            title="Restricted Doc", audiences=[AudienceFactory(groups=[group])]
        )
        ApprovedRevisionFactory(document=restricted, content="Secret content")

        # Audience IDs are compared, not their groups: an audience with the same group
        # is still a different audience.
        including = DocumentFactory(
            title="Other Audience Doc", audiences=[AudienceFactory(groups=[group])]
        )
        ApprovedRevisionFactory(document=including)
        p = self._make_parser(including)
        doc = pq(p.parse("[[Include:Restricted Doc]]"))
        self.assertNotIn("Secret content", doc.text())

    def test_include_restricted_document_without_source_context(self):
        """Restricted includes should be blocked when there is no source document context."""
        restricted = DocumentFactory(title="Restricted Doc", audiences=[AudienceFactory()])
        ApprovedRevisionFactory(document=restricted, content="Secret content")

        # No source doc — e.g., parsing from questions, forums, or a brand-new doc preview.
        p = WikiParser()
        doc = pq(p.parse("[[Include:Restricted Doc]]"))
        self.assertNotIn("Secret content", doc.text())

    def test_include_restricted_translation_from_unrestricted(self):
        """Including a translation of a restricted doc should be blocked for unrestricted sources."""
        parent = DocumentFactory(title="Restricted Doc", audiences=[AudienceFactory()])
        ApprovedRevisionFactory(document=parent, content="Secret content")

        translation = DocumentFactory(title="Restricted Doc", locale="fr", parent=parent)
        ApprovedRevisionFactory(document=translation, content="Contenu secret")

        unrestricted = DocumentFactory(title="Public Doc")
        ApprovedRevisionFactory(document=unrestricted)
        p = self._make_parser(unrestricted)
        doc = pq(p.parse("[[Include:Restricted Doc]]", locale="fr"))
        self.assertNotIn("Contenu secret", doc.text())

    def test_include_restricted_translation_from_same_audience(self):
        """Including a translation of a restricted doc should work when audiences match."""
        audience = AudienceFactory()
        parent = DocumentFactory(title="Restricted Doc", audiences=[audience])
        ApprovedRevisionFactory(document=parent, content="Secret content")

        translation = DocumentFactory(title="Restricted Doc", locale="fr", parent=parent)
        ApprovedRevisionFactory(document=translation, content="Contenu secret")

        including = DocumentFactory(title="Also Restricted", audiences=[audience])
        ApprovedRevisionFactory(document=including)
        p = self._make_parser(including)
        doc = pq(p.parse("[[Include:Restricted Doc]]", locale="fr"))
        self.assertEqual("Contenu secret", doc.text())


class TestWikiTemplateRestricted(TestCase):
    def _make_parser(self, source_doc):
        """Helper to create a WikiParser with the restriction context of a source document."""
        return WikiParser(
            doc_id=source_doc.id,
            audience_ids=source_doc.original.private_audience_ids,
        )

    def test_template_restricted_from_unrestricted(self):
        """An unrestricted doc using a restricted template should not reveal its content."""
        restricted = TemplateDocumentFactory(audiences=[AudienceFactory()])
        template_name = restricted.title.removeprefix(TEMPLATE_TITLE_PREFIX)
        ApprovedRevisionFactory(document=restricted, content="Secret template content")

        unrestricted = DocumentFactory(title="Public Doc")
        ApprovedRevisionFactory(document=unrestricted)
        p = self._make_parser(unrestricted)
        doc = pq(p.parse(f"[[Template:{template_name}]]"))
        self.assertNotIn("Secret template content", doc.text())

    def test_template_restricted_from_same_audience(self):
        """A restricted doc using a template with the same audience should work."""
        audience = AudienceFactory()
        restricted = TemplateDocumentFactory(audiences=[audience])
        template_name = restricted.title.removeprefix(TEMPLATE_TITLE_PREFIX)
        ApprovedRevisionFactory(document=restricted, content="Secret template content")

        including = DocumentFactory(title="Also Restricted", audiences=[audience])
        ApprovedRevisionFactory(document=including)
        p = self._make_parser(including)
        doc = pq(p.parse(f"[[Template:{template_name}]]"))
        self.assertIn("Secret template content", doc.text())


class TestWikiVideo(TestCase):
    """Video hook."""

    def test_video_not_exist(self):
        """Video does not exist."""
        p = WikiParser()
        doc = pq(p.parse("[[V:404]]", locale="fr"))
        self.assertEqual("La vidéo « 404 » n’existe pas.", doc.text().replace("\xa0", " "))

    def test_youtube_video(self):
        """Verify youtube embeds."""
        urls = [
            "http://www.youtube.com/watch?v=oHg5SJYRHA0",
            "https://youtube.com/watch?v=oHg5SJYRHA0",
            "http://youtu.be/oHg5SJYRHA0",
            "https://youtu.be/oHg5SJYRHA0",
        ]
        parser = WikiParser()

        for url in urls:
            with self.subTest(url):
                doc = pq(parser.parse("[[V:{}]]".format(url)))
                assert (
                    doc("iframe")[0]
                    .attrib["src"]
                    .startswith("//www.youtube.com/embed/oHg5SJYRHA0")
                )


class ForWikiTests(TestCase):
    """Tests for the wiki implementation of the {for} directive, which
    arranges for certain parts of the page to show only when viewed on certain
    OSes or browser versions"""

    def test_rendering(self):
        cases = [
            # A {for} set off by itself or wrapping a block-level element is block-level.
            (
                "Joe\n\n{for}Red{/for}\n\nBlow",
                '<p>Joe</p><p><span class="for">Red</span></p><p>Blow</p>',
            ),
            (
                "Joe\n\n{for}\n* Red\n{/for}\n\nBlow",
                '<p>Joe</p><div class="for"><ul><li> Red</li></ul></div><p>Blow</p>',
            ),
            (
                "Joe\n\nRed {for}riding{/for} hood\n\nBlow",
                '<p>Joe</p><p>Red <span class="for">riding</span> hood</p><p>Blow</p>',
            ),
            (
                "{for mac}\nJoe\n\nRed {for}{for}riding\n{/for} hood{/for}\n\nBlow\n{/for}",
                '<div data-for="mac" class="for">'
                "<p>Joe</p>"
                '<p>Red <span class="for"><span class="for">riding'
                "</span> hood</span></p>"
                "<p>Blow</p>"
                "</div>",
            ),
            (
                "{for mac,linux,3.6}One{/for}",
                '<p><span class="for" data-for="mac,linux,3.6">One</span></p>',
            ),
            # Early closer.
            (
                "{for}\nOne\n\n*Fish{/for}",
                '<div class="for"><p>One</p><ul><li>Fish</li></ul></div>',
            ),
            # Closer after the enclosing element closes: close just before it.
            (
                "*{for}One\n*Fish\n\nTwo\n{/for}",
                '<ul><li><span class="for">One</span></li><li>Fish</li></ul><p>Two</p>',
            ),
            # Missing closer: close just before the enclosing element.
            (
                "{for}One fish\n\nTwo fish",
                '<p><span class="for">One fish</span></p><p>Two fish</p>',
            ),
            (
                "{for}Vous parl\u00e9 Fran\u00e7ais{/for}",
                '<p><span class="for">Vous parl\u00e9 Fran\u00e7ais</span></p>',
            ),
            # Empty attributes don't raise.
            (
                '<p><video controls="" height="120">'
                '  <source src="/some/path/file.ogv" type="video/ogv">'
                "</video></p>",
                '<p><video controls height="120">'
                '  <source src="/some/path/file.ogv" type="video/ogv">'
                "</video></p>",
            ),
            (
                "{for}\n"
                "=H1=\n"
                "==H2==\n"
                "Llamas are fun:\n"
                "\n"
                "*Jumping\n"
                "*Rolling\n"
                "*Grazing\n"
                "\n"
                "They have high melting points.\n"
                "{/for}",
                '<div class="for"><h1 id="w_h1">H1</h1>'
                '<h2 id="w_h2">H2</h2><p>Llamas are fun:</p>'
                "<ul><li>Jumping</li><li>Rolling</li><li>Grazing</li></ul>"
                "<p>They have high melting points.</p></div>",
            ),
        ]
        for wiki, html in cases:
            with self.subTest(wiki=wiki):
                self.assertHTMLEqual(WikiParser().parse(wiki), html)

    def test_adjacent_blocks(self):
        """Make sure one block-level {for} doesn't absorb an adjacent one."""
        p = WikiParser()
        html = p.parse(
            "{for fx4}\n{for mac}Fx4{/for}\n{/for}\n{for fx3}\n{for mac}Fx3{/for}\n{/for}"
        )
        # The two div.fors should be siblings, not nested:
        self.assertEqual([], pq(html)("div.for div.for"))

    def test_leading_newlines(self):
        """Make sure leading newlines don't cause a block-level {for} to be
        sucked into the leading blank paragraph, causing the actual text to
        always be shown."""
        doc = pq(WikiParser().parse("\n\n{for linux}\nunixify\n{/for}"))
        self.assertEqual("unixify", doc(".for").text().strip())

    def test_block_level_section(self):
        """Make sure we recognize <section> as a block element."""
        p = WikiParser()
        html = p.parse("{for}<section>hi</section>{/for}")
        assert "<div" in html, "Didn't detect <section> tag as block level"


class ForParserTests(TestCase):
    """Tests for the ForParser

    These are unit tests for ForParser, and ForWikiTests are
    (as a bonus) integration tests for it.

    """

    def test_balancing(self):
        """Tags come out balanced, with misplaced or missing for closers fixed."""
        cases = [
            ('<ul><li class="1"><br><for>One</for></li></ul>', None),
            # Text chunks interspersed with tags.
            ("<p>Hello<br>there, <br>you.</p>", None),
            ("<for>Vous parl\u00e9 Fran\u00e7ais</for>", None),
            # A leading naked run of text, and inner runs.
            ("A<i>hi</i>B<i>there</i>C", None),
            # Self-closing tags aren't balanced as paired ones.
            ('<img src="smoo"><span>g</span>', None),
            ('<img src="smoo"/><span>g</span>', '<img src="smoo"><span>g</span>'),
            # Early closer.
            ("<div><for><p>One</for></for></p></div>", "<div><for><p>One</p></for></div>"),
            # Late closer: close just before the enclosing element.
            (
                "<ul><li><for><for>One</li></ul></for>",
                "<ul><li><for><for>One</for></for></li></ul>",
            ),
            # For tags left open at the end.
            ("<for><p>One</for></for></p>", "<for><p>One</p></for>"),
        ]
        for html, want in cases:
            with self.subTest(html=html):
                self.assertEqual(want or html, str(ForParser(html)))

    def test_expansion(self):
        """Fors with block content become divs, others spans, keeping data- attributes."""
        for html, want in (
            ("<for><p>One</p></for>", '<div class="for"><p>One</p></div>'),
            ("<for><em>One</em></for>", '<span class="for"><em>One</em></span>'),
            (
                '<for data-for="mac,linux">One</for>',
                '<span class="for" data-for="mac,linux">One</span>',
            ),
        ):
            with self.subTest(html=html):
                expander = ForParser(html)
                expander.expand_fors()
                self.assertEqual(want, str(expander))

    def test_on_own_line(self):
        def on_own_line_eq(want, text):
            """Assert that on_own_line operates as expected on the first match
            in `text`."""
            match = ForParser._FOR_OR_CLOSER.search(text)
            self.assertEqual(want, ForParser._on_own_line(match, match.groups(3)))

        on_own_line_eq((True, True, True), "{for}")
        on_own_line_eq((True, True, True), "{for} ")
        on_own_line_eq((False, False, True), " {for}")
        on_own_line_eq((True, False, True), "q\n{for}")
        on_own_line_eq((False, True, False), "{for}q")
        on_own_line_eq((True, False, False), "\n{for} \nq")

    def test_strip(self):
        cases = [
            ("{for}inline{/for}", "\x910\x91inline\x91/sf\x91"),
            ("{for}\nblock\n{/for}", "\x910\x91\n\nblock\n\n\x91/sf\x91"),
            ("{for}inline\n{/for}", "\x910\x91inline\n\n\x91/sf\x91"),
            ("{for}\nblock{/for}", "\x910\x91\n\nblock\x91/sf\x91"),
            # Newlines preceding the current match count toward its prespace.
            (
                "{for}\n{for}inline{/for}\n{/for}",
                "\x910\x91\n\n\x911\x91inline\x91/sf\x91\n\n\x91/sf\x91",
            ),
            # Each lookbehind sees the whitespace earlier replacements added.
            (
                "{for fx4}\n{for mac}Fx4{/for}\n{/for}\n{for fx3}\n{for mac}Fx3{/for}\n{/for}",
                "\x910\x91\n\n\x911\x91Fx4\x91/sf\x91\n\n\x91/sf\x91\n\n"
                "\x912\x91\n\n\x913\x91Fx3\x91/sf\x91\n\n\x91/sf\x91",
            ),
        ]
        for text, want in cases:
            with self.subTest(text=text):
                self.assertEqual(want, ForParser.strip_fors(text)[0])


class WhatLinksHereTests(TestCase):
    def test_links(self):
        d1, _, _ = doc_rev_parser("", title="D1")
        d2, _, _ = doc_rev_parser("[[D1]]", title="D2")
        d3, _, _ = doc_rev_parser("[[D1]] [[D2]]", title="D3")

        self.assertEqual(len(d1.links_to()), 2)
        self.assertEqual(len(d1.links_from()), 0)
        self.assertEqual(len(d2.links_to()), 1)
        self.assertEqual(len(d2.links_from()), 1)
        self.assertEqual(len(d3.links_to()), 0)
        self.assertEqual(len(d3.links_from()), 2)

        self.assertEqual([d.linked_from.title for d in d1.links_to()], ["D2", "D3"])
        self.assertEqual([d.kind for d in d1.links_to()], ["link", "link"])
        self.assertEqual([d.linked_from.title for d in d2.links_to()], ["D3"])

    def test_templates(self):
        d1, _, _ = doc_rev_parser(
            "Oh hai", title=TEMPLATE_TITLE_PREFIX + "D1", category=TEMPLATES_CATEGORY
        )
        d2, _, _ = doc_rev_parser("[[Template:D1]]", title="D2")

        self.assertEqual(len(d1.links_to()), 1)
        self.assertEqual(len(d1.links_from()), 0)
        self.assertEqual(len(d2.links_to()), 0)
        self.assertEqual(len(d2.links_from()), 1)

        self.assertEqual(d1.links_to()[0].kind, "template")

    def test_includes(self):
        d1, _, _ = doc_rev_parser("Oh hai", title="D1")
        d2, _, _ = doc_rev_parser("[[Include:D1]]", title="D2")

        self.assertEqual(len(d1.links_to()), 1)
        self.assertEqual(len(d1.links_from()), 0)
        self.assertEqual(len(d2.links_to()), 0)
        self.assertEqual(len(d2.links_from()), 1)

        self.assertEqual(d1.links_to()[0].kind, "include")

    def test_duplicates(self):
        """Document.links_to and Document.links_from should only count
        documents that link, not every instance of a link on a page.
        Make sure that things work that way."""
        d1, _, _ = doc_rev_parser("", title="D1")
        d2, _, _ = doc_rev_parser("[[D1]] [[D1]] [[D1]]", title="D2")

        self.assertEqual(len(d1.links_to()), 1)
        self.assertEqual(len(d1.links_from()), 0)
        self.assertEqual(len(d2.links_to()), 0)
        self.assertEqual(len(d2.links_from()), 1)

        self.assertEqual(d1.links_to()[0].kind, "link")

    def test_locales_exists(self):
        """Links should use the correct locale."""
        d1 = DocumentFactory(title="Foo", locale="en-US")
        RevisionFactory(document=d1, content="", is_approved=True)
        d2 = DocumentFactory(title="Foo", locale="de")
        RevisionFactory(document=d2, content="", is_approved=True)
        d3 = DocumentFactory(title="Bar", locale="de")
        RevisionFactory(document=d3, content="[[Foo]]", is_approved=True)

        self.assertEqual(len(d1.links_to()), 0)
        self.assertEqual(len(d1.links_from()), 0)
        self.assertEqual(len(d2.links_to()), 1)
        self.assertEqual(len(d2.links_from()), 0)
        self.assertEqual(len(d3.links_to()), 0)
        self.assertEqual(len(d3.links_from()), 1)

        self.assertEqual(d2.links_to()[0].kind, "link")

    def test_locales_renames(self):
        """Links should use the correct locale, even if the title has
        been translated."""
        d1 = DocumentFactory(title="Foo", locale="en-US")
        RevisionFactory(document=d1, content="", is_approved=True)
        d2 = DocumentFactory(title="German Foo", locale="de", parent=d1)
        RevisionFactory(document=d2, content="", is_approved=True)
        d3 = DocumentFactory(title="German Bar", locale="de")
        RevisionFactory(document=d3, content="[[Foo]]", is_approved=True)

        self.assertEqual(len(d1.links_to()), 0)
        self.assertEqual(len(d1.links_from()), 0)
        self.assertEqual(len(d2.links_to()), 1)
        self.assertEqual(len(d2.links_from()), 0)
        self.assertEqual(len(d3.links_to()), 0)
        self.assertEqual(len(d3.links_from()), 1)

        self.assertEqual(d2.links_to()[0].kind, "link")

    def test_unicode(self):
        """Unicode is hard. Test that."""
        # \u03C0 is pi and \u2764 is a heart symbol.
        d1 = DocumentFactory(title="\u03c0", slug="pi")
        ApprovedRevisionFactory(document=d1, content="I \u2764 \u03c0")
        d2 = DocumentFactory(title="\u2764", slug="heart")
        ApprovedRevisionFactory(document=d2, content="What do you think about [[\u03c0]]?")

        self.assertEqual(len(d1.links_to()), 1)
        self.assertEqual(len(d1.links_from()), 0)
        self.assertEqual(len(d2.links_to()), 0)
        self.assertEqual(len(d2.links_from()), 1)

        self.assertEqual(d1.links_to()[0].kind, "link")

    def test_old_revisions(self):
        """Bug 862436. Updating old revisions could cause bad WLH data."""
        d1 = DocumentFactory(title="D1")
        RevisionFactory(document=d1, content="", is_approved=True)
        d2 = DocumentFactory(title="D2")
        RevisionFactory(document=d2, content="", is_approved=True)

        # Make D3, then make a revision that links to D1, then a
        # revision that links to D2. Only the link to D2 should count.
        d3 = DocumentFactory(title="D3")
        r3_old = ApprovedRevisionFactory(document=d3, content="[[D1]]")
        ApprovedRevisionFactory(document=d3, content="[[D2]]")

        # This could cause stale data
        r3_old.content_parsed

        # D1 is not linked to in any current revisions.
        self.assertEqual(len(d1.links_to()), 0)
        self.assertEqual(len(d1.links_from()), 0)
        self.assertEqual(len(d2.links_to()), 1)
        self.assertEqual(len(d2.links_from()), 0)
        self.assertEqual(len(d3.links_to()), 0)
        self.assertEqual(len(d3.links_from()), 1)

    def test_images(self):
        """Each distinct image is recorded once, however often the article embeds it."""
        img = ImageFactory(title="image-file.png")
        other = ImageFactory(title="other.png")
        d1, _, _ = doc_rev_parser(
            "[[Image:image-file.png]] [[Image:other.png]] [[Image:image-file.png]]", title="D1"
        )

        self.assertCountEqual(d1.images, [img, other])
        self.assertEqual(list(img.documents()), [d1])


class TestLazyWikiImageTags(TestCase):
    def setUp(self):
        self.d, self.r, self.p = doc_rev_parser("Test content", "Installing Firefox")
        self.img = ImageFactory(title="test.jpg")

    def tearDown(self):
        self.img.delete()

    def test_simple(self):
        """Simple image tag markup."""
        doc = pq(self.p.parse("[[Image:test.jpg]]", locale=settings.WIKI_DEFAULT_LANGUAGE))
        img = doc("img")
        self.assertEqual("test.jpg", img.attr("alt"))
        self.assertEqual(self.img.file.url, img.attr("data-original-src"))
        self.assertRegex(img.attr("src"), r"placeholder\.[0-9a-z]+\.gif")


class TestWikiPrivateImages(TemporaryMediaRoots, TestCase):
    """An image resolves in the article's own knowledge base first, then in the default one."""

    def setUp(self):
        super().setUp()
        self.kbs = {
            "foo": AudienceFactory(name="foo"),
            "bar": AudienceFactory(name="bar"),
            "default": Audience.objects.default(),
        }

    @parameterized.expand(
        [
            ("own_kb_image_wins_over_default", ["foo"], ["foo", "default"], "foo"),
            ("default_image", ["foo"], ["default"], "default"),
            ("other_kb_image", ["bar"], ["foo"], None),
            ("several_kbs_use_default_only", ["foo", "bar"], ["foo", "default"], "default"),
            ("no_kb_uses_default_only", [], ["foo"], None),
            ("public_article_uses_default_only", ["default"], ["foo"], None),
        ]
    )
    def test_stored_document_html(self, _name, article_kbs, image_kbs, rendered_kb):
        images = {kb: ImageFactory(title="Shot", audience=self.kbs[kb]) for kb in image_kbs}
        document = DocumentFactory(audiences=[self.kbs[kb] for kb in article_kbs])
        ApprovedRevisionFactory(document=document, content="[[Image:Shot]]")
        document.refresh_from_db()

        if rendered_kb is None:
            self.assertIn('The image "Shot" does not exist.', document.html)
            self.assertNotIn("<img", document.html)
            return

        src = pq(document.html)("img").attr("data-original-src")
        self.assertEqual(images[rendered_kb].file.url, src)
        self.assertEqual(rendered_kb != "default", src.startswith("/private-media/private/"))

    def test_translation_prefers_its_knowledge_bases_english_image(self):
        image = ImageFactory(title="Shot", audience=self.kbs["foo"], locale="en-US")
        ImageFactory(title="Shot", audience=self.kbs["default"], locale="de")
        parent = DocumentFactory(audiences=[self.kbs["foo"]])
        ApprovedRevisionFactory(document=parent)
        translation = DocumentFactory(locale="de", parent=parent)
        ApprovedRevisionFactory(document=translation, content="[[Image:Shot]]")
        translation.refresh_from_db()

        self.assertEqual(image.file.url, pq(translation.html)("img").attr("data-original-src"))

    def test_document_images_record_only_the_images_the_lookup_found(self):
        found = ImageFactory(title="Shot", audience=self.kbs["foo"])
        ImageFactory(title="Other", audience=self.kbs["bar"])
        document = DocumentFactory(audiences=[self.kbs["foo"]])
        ApprovedRevisionFactory(document=document, content="[[Image:Shot]] [[Image:Other]]")

        self.assertEqual([found], list(document.images))

    def test_public_image_costs_one_query(self):
        ImageFactory(title="Shot")

        with self.assertNumQueries(1):
            html = WikiParser().parse("[[Image:Shot]]")

        self.assertIn("<img", html)


class TestWikiUIComponent(TestCase):
    """Test the UI Component hook."""

    def test_ui_component(self):
        """Verify that the UI component hook works."""
        parser = WikiParser()
        dmw = '<input type="text" id="x" name="x">'
        content_template = "<p>before</p>{}<p>after</p>"
        with patch("kitsune.sumo.parser.generate_ui_component_embed", return_value=dmw):
            result = parser.parse(content_template.format("[[UI:device_migration_wizard]]"))
            self.assertEqual(result, content_template.format(dmw))

    def test_invalid_ui_component(self):
        """Verify error message shown for invalid UI component requests."""
        parser = WikiParser()
        content_template = "<p>before</p>{}<p>after</p>"
        result = parser.parse(content_template.format("[[UI:undefined]]"))
        self.assertEqual(
            result,
            content_template.format('The UI component "undefined" does not exist.'),
        )
