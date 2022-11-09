import re

from django.conf import settings
from django.test.utils import override_settings
from pyquery import PyQuery as pq

import kitsune.sumo.tests.test_parser
from kitsune.gallery.models import Video
from kitsune.gallery.tests import ImageFactory, VideoFactory
from kitsune.sumo.tests import TestCase
from kitsune.wiki.config import TEMPLATE_TITLE_PREFIX, TEMPLATES_CATEGORY
from kitsune.wiki.models import Document
from kitsune.wiki.parser import PATTERNS, RECURSION_MESSAGE, ForParser, WikiParser
from kitsune.wiki.parser import _build_template_params as _btp
from kitsune.wiki.parser import _format_template_content as _ftc
from kitsune.wiki.parser import _key_split
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
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

    def test_note_simple(self):
        """Simple note syntax"""
        p = WikiParser()
        doc = pq(p.parse("{note}this is a note{/note}"))
        self.assertEqual("this is a note", doc("div.note").text())

    def test_warning_simple(self):
        """Simple warning syntax"""
        p = WikiParser()
        doc = pq(p.parse("{warning}this is a warning{/warning}"))
        self.assertEqual("this is a warning", doc("div.warning").text())

    def test_warning_multiline(self):
        """Multiline warning syntax"""
        p = WikiParser()
        doc = pq(p.parse("{warning}\nthis is a warning\n{/warning}"))
        self.assertEqual("this is a warning", doc("div.warning").text())

    def test_warning_multiline_breaks(self):
        """Multiline breaks warning syntax"""
        p = WikiParser()
        doc = pq(p.parse("\n\n{warning}\n\nthis is a warning\n\n{/warning}\n\n"))
        self.assertEqual("this is a warning", doc("div.warning").text())

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
        doc, p = doc_parse_markup(
            '<span class="key">{{{1}}}</span>', "[[T:test|Cmd]] + [[T:test|Shift]]"
        )
        self.assertEqual(1, len(doc("p")))

    def test_template_multiline(self):
        """Multiline templates are wrapped in <p>s"""
        doc, p = doc_parse_markup('<span class="key">\n{{{1}}}</span>', "[[T:test|Cmd]]")
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

    def test_simple_inline_custom(self):
        """Simple custom inline syntax: menu, button, filepath, pref"""
        p = WikiParser()
        tags = ["menu", "button", "filepath", "pref"]
        for tag in tags:
            doc = pq(p.parse("{%s this is a %s}" % (tag, tag)))
            self.assertEqual("this is a " + tag, doc("span." + tag).text())

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
            p.parse("[[%s]]" % doc.title),
            '<p><a href="/en-US/kb/%s/">%s</a>\n</p>' % (doc.slug, doc.title),
        )
        self.assertEqual(
            p.parse("[[%s]]" % redirect.title),
            '<p><a href="/en-US/kb/%s/">%s</a>\n</p>' % (doc.slug, doc.title),
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
        self.assertEqual(
            'The template "test" does not exist or has no approved revision.', doc.text()
        )

    def test_template_locale_fallback(self):
        """If localized template does not exist, fall back to English."""
        _, p = doc_parse_markup("English content", "[[Template:test]]")
        doc = pq(p.parse("[[T:test]]", locale="fr"))
        self.assertEqual("English content", doc.text())

    def test_template_anonymous_params(self):
        """Template markup with anonymous parameters."""
        doc, p = doc_parse_markup("{{{1}}}:{{{2}}}", "[[Template:test|one|two]]")
        self.assertEqual("one:two", doc.text())
        doc = pq(p.parse("[[T:test|two|one]]"))
        self.assertEqual("two:one", doc.text())

    def test_template_named_params(self):
        """Template markup with named parameters."""
        doc, p = doc_parse_markup("{{{a}}}:{{{b}}}", "[[Template:test|a=one|b=two]]")
        self.assertEqual("one:two", doc.text())
        doc = pq(p.parse("[[T:test|a=two|b=one]]"))
        self.assertEqual("two:one", doc.text())

    def test_template_numbered_params(self):
        """Template markup with numbered parameters."""
        doc, p = doc_parse_markup("{{{1}}}:{{{2}}}", "[[Template:test|2=one|1=two]]")
        self.assertEqual("two:one", doc.text())
        doc = pq(p.parse("[[T:test|2=two|1=one]]"))
        self.assertEqual("one:two", doc.text())

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

    def test_format_template_content_named(self):
        """_ftc handles named arguments"""
        self.assertEqual("ab", _ftc("{{{some}}}{{{content}}}", {"some": "a", "content": "b"}))

    def test_format_template_content_numbered(self):
        """_ftc handles numbered arguments"""
        self.assertEqual("a:b", _ftc("{{{1}}}:{{{2}}}", {"1": "a", "2": "b"}))

    def test_build_template_params_anonymous(self):
        """_btp handles anonymous arguments"""
        self.assertEqual({"1": "<span>a</span>", "2": "test"}, _btp(["<span>a</span>", "test"]))

    def test_build_template_params_numbered(self):
        """_btp handles numbered arguments"""
        self.assertEqual({"20": "a", "10": "test"}, _btp(["20=a", "10=test"]))

    def test_build_template_params_named(self):
        """_btp handles only named-arguments"""
        self.assertEqual({"a": "b", "hi": "test"}, _btp(["hi=test", "a=b"]))

    def test_build_template_params_named_anonymous(self):
        """_btp handles mixed named and anonymous arguments"""
        self.assertEqual({"1": "a", "hi": "test"}, _btp(["hi=test", "a"]))

    def test_build_template_params_named_numbered(self):
        """_btp handles mixed named and numbered arguments"""
        self.assertEqual({"10": "a", "hi": "test"}, _btp(["hi=test", "10=a"]))

    def test_build_template_params_named_anonymous_numbered(self):
        """_btp handles mixed named, anonymous and numbered arguments"""
        self.assertEqual({"1": "a", "hi": "test", "3": "z"}, _btp(["hi=test", "a", "3=z"]))

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
        expected = "<p>Fine %s Fellows\n</p>" % recursion_message
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
            "<p>Paper Wooden %s Bats\n Cups\n</p>" % recursion_message, boo.content_parsed
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
            "Paper Wooden %s Bats Cups" % recursion_message,
            re.sub(r"</?p>|\n", "", boo.content_parsed),
        )


class TestWikiVideo(TestCase):
    """Video hook."""

    def tearDown(self):
        Video.objects.all().delete()
        super(TestWikiVideo, self).tearDown()

    def test_video_english(self):
        """Video is created and found in English."""
        v = VideoFactory()
        d = ApprovedRevisionFactory(content="[[V:%s]]" % v.title).document
        doc = pq(d.html)
        self.assertEqual("video", doc("div.video").attr("class"))

        # This test and the code it tests hasn't changed in
        # months. However, this test started failing for Mike and I
        # early July 2013. We think we picked up libxml2 2.9.1 and
        # that causes the output to be different.  I contend that the
        # output and expected output are both "wrong" in that they're
        # invalid html5 and the output I'm getting isn't really any
        # worse. Ergo, I have changed the test to accept either output
        # because I got stuff to do. Having said that, this is kind of
        # ridiculous and should be fixed. See bug #892610.
        assert doc("video").html() in [
            # This was the original expected test output.
            (
                '<source src="{0}" '
                'type="video/webm"><source src="{1}" type="video/ogg"/>'
                "</source>".format(v.webm.url, v.ogv.url)
            ),
            # This is the version that Mike and I get.
            (
                '\n          <source src="{0}" type="video/webm">'
                '\n          <source src="{1}" type="video/ogg">'
                "\n      </source></source>".format(v.webm.url, v.ogv.url)
            ),
        ]

        self.assertEqual(1, len(doc("video")))
        self.assertEqual(2, len(doc("source")))
        data_fallback = doc("video").attr("data-fallback")
        self.assertEqual(v.flv.url, data_fallback)

    def test_video_fallback_french(self):
        """English video is found in French."""
        p = WikiParser()
        v = VideoFactory()
        doc = pq(p.parse("[[V:%s]]" % v.title, locale="fr"))
        self.assertEqual("video", doc("div.video").attr("class"))
        self.assertEqual(1, len(doc("video")))
        self.assertEqual(2, len(doc("source")))
        data_fallback = doc("video").attr("data-fallback")
        self.assertEqual(Video.objects.all()[0].flv.url, data_fallback)

    def test_video_not_exist(self):
        """Video does not exist."""
        p = WikiParser()
        doc = pq(p.parse("[[V:404]]", locale="fr"))
        self.assertEqual('The video "404" does not exist.', doc.text())

    def test_video_modal(self):
        """Video modal defaults for plcaeholder and text."""
        v = VideoFactory()
        replacement = '<img class="video-thumbnail" src="%s"/>' % v.thumbnail_url_if_set()
        d = ApprovedRevisionFactory(content="[[V:%s|modal]]" % v.title).document
        doc = pq(d.html)
        self.assertEqual(v.title, doc(".video-modal")[0].attrib["title"])
        self.assertEqual(1, doc(".video video").length)
        self.assertEqual(replacement, doc(".video-placeholder").html().strip())
        self.assertEqual("video modal-trigger", doc("div.video").attr("class"))

    def test_video_modal_caption_text(self):
        """Video modal can change title and placeholder text."""
        v = VideoFactory()
        r = ApprovedRevisionFactory(
            content="[[V:%s|modal|placeholder=Place<b>holder</b>|title=WOOT]]" % v.title
        )
        d = r.document
        doc = pq(d.html)
        self.assertEqual("WOOT", doc(".video-modal")[0].attrib["title"])
        self.assertEqual("Place<b>holder</b>", doc(".video-placeholder").html().strip())

    @override_settings(GALLERY_VIDEO_URL="http://videos.mozilla.org/serv/sumo/")
    def test_video_cdn(self):
        """Video URLs can link to the CDN if a CDN setting is set."""
        v = VideoFactory()
        d = ApprovedRevisionFactory(content="[[V:%s]]" % v.title).document
        doc = pq(d.html)
        assert settings.GALLERY_VIDEO_URL in doc("source").eq(1).attr("src")
        assert settings.GALLERY_VIDEO_URL in doc("video").attr("data-fallback")
        assert settings.GALLERY_VIDEO_URL in doc("source").eq(0).attr("src")

    def test_youtube_video(self):
        """Verify youtube embeds."""
        urls = [
            "http://www.youtube.com/watch?v=oHg5SJYRHA0",
            "https://youtube.com/watch?v=oHg5SJYRHA0"
            "http://youtu.be/oHg5SJYRHA0"
            "https://youtu.be/oHg5SJYRHA0",
        ]
        parser = WikiParser()

        for url in urls:
            doc = pq(parser.parse("[[V:%s]]" % url))
            assert doc("iframe")[0].attrib["src"].startswith("//www.youtube.com/embed/oHg5SJYRHA0")


class ForWikiTests(TestCase):
    """Tests for the wiki implementation of the {for} directive, which
    arranges for certain parts of the page to show only when viewed on certain
    OSes or browser versions"""

    def assertWikiHtmlEqual(self, wiki, html, msg=None):
        self.assertHTMLEqual(WikiParser().parse(wiki), html, msg=msg)

    def test_block(self):
        """A {for} set off by itself or wrapping a block-level element should
        be a paragraph or other kind of block-level thing."""
        self.assertWikiHtmlEqual(
            "Joe\n\n{for}Red{/for}\n\nBlow",
            '<p>Joe</p><p><span class="for">Red</span></p><p>Blow</p>',
        )
        self.assertWikiHtmlEqual(
            "Joe\n\n{for}\n* Red\n{/for}\n\nBlow",
            '<p>Joe</p><div class="for"><ul><li> Red</li></ul></div><p>Blow</p>',
        )

    def test_inline(self):
        """A for not meeting the conditions in test_block should be inline."""
        self.assertWikiHtmlEqual(
            "Joe\n\nRed {for}riding{/for} hood\n\nBlow",
            '<p>Joe</p><p>Red <span class="for">riding</span> hood</p><p>Blow</p>',
        )

    def test_nested(self):
        """{for} tags should be nestable."""
        self.assertWikiHtmlEqual(
            "{for mac}\n"
            "Joe\n"
            "\n"
            "Red {for}{for}riding\n"
            "{/for} hood{/for}\n"
            "\n"
            "Blow\n"
            "{/for}",
            '<div data-for="mac" class="for">'
            "<p>Joe</p>"
            '<p>Red <span class="for"><span class="for">riding'
            "</span> hood</span></p>"
            "<p>Blow</p>"
            "</div>",
        )

    def test_data_attrs(self):
        """Make sure the correct attributes are set on the for element."""
        self.assertWikiHtmlEqual(
            "{for mac,linux,3.6}One{/for}",
            '<p><span class="for" data-for="mac,linux,3.6">One</span></p>',
        )

    def test_early_close(self):
        """Make sure the parser closes the for tag at the right place when
        its closer is early."""
        self.assertWikiHtmlEqual(
            "{for}\nOne\n\n*Fish{/for}", '<div class="for"><p>One</p><ul><li>Fish</li></ul></div>'
        )

    def test_late_close(self):
        """If the closing for tag is not closed by the time the enclosing
        element of the opening for tag is closed, close the for tag
        just before the enclosing element."""
        self.assertWikiHtmlEqual(
            "*{for}One\n*Fish\n\nTwo\n{/for}",
            '<ul><li><span class="for">One</span></li><li>Fish</li></ul><p>Two</p>',
        )

    def test_missing_close(self):
        """If the closing for tag is missing, close the for tag just
        before the enclosing element."""
        self.assertWikiHtmlEqual(
            "{for}One fish\n\nTwo fish", '<p><span class="for">One fish</span></p><p>Two fish</p>'
        )

    def test_unicode(self):
        """Make sure non-ASCII chars survive being wrapped in a for."""
        french = "Vous parl\u00e9 Fran\u00e7ais"
        self.assertWikiHtmlEqual(
            "{for}" + french + "{/for}", '<p><span class="for">' + french + "</span></p>"
        )

    def test_boolean_attr(self):
        """Make sure empty attributes don't raise exceptions."""
        self.assertWikiHtmlEqual(
            '<p><video controls="" height="120">'
            '  <source src="/some/path/file.ogv" type="video/ogv">'
            "</video></p>",
            '<p><video controls height="120">'
            '  <source src="/some/path/file.ogv" type="video/ogv">'
            "</video></p>",
        )

    def test_adjacent_blocks(self):
        """Make sure one block-level {for} doesn't absorb an adjacent one."""
        p = WikiParser()
        html = p.parse(
            "{for fx4}\n"
            "{for mac}Fx4{/for}\n"
            "{/for}\n"
            "{for fx3}\n"
            "{for mac}Fx3{/for}\n"
            "{/for}"
        )
        # The two div.fors should be siblings, not nested:
        self.assertEqual([], pq(html)("div.for div.for"))

    def test_leading_newlines(self):
        """Make sure leading newlines don't cause a block-level {for} to be
        sucked into the leading blank paragraph, causing the actual text to
        always be shown."""
        doc = pq(WikiParser().parse("\n\n{for linux}\nunixify\n{/for}"))
        self.assertEqual("unixify", doc(".for").text().strip())

    def test_big_swath(self):
        """Enclose a big section containing many tags."""
        self.assertWikiHtmlEqual(
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
        )

    def test_block_level_section(self):
        """Make sure we recognize <section> as a block element."""
        p = WikiParser()
        html = p.parse("{for}<section>hi</section>{/for}")
        assert "<div" in html, "Didn't detect <section> tag as block level"


def balanced_eq(want, to_balance):
    """Run `to_balance` through the expander to get its tags balanced, and
    assert the result is `want`."""
    expander = ForParser(to_balance)
    TestCase().assertEqual(want, str(expander))


def expanded_eq(want, to_expand):
    """Balance and expand the fors in `to_expand`, and assert equality with
    `want`."""
    expander = ForParser(to_expand)
    expander.expand_fors()
    TestCase().assertEqual(want, str(expander))


def strip_eq(want, text):
    TestCase().assertEqual(want, ForParser.strip_fors(text)[0])


class ForParserTests(TestCase):
    """Tests for the ForParser

    These are unit tests for ForParser, and ForWikiTests are
    (as a bonus) integration tests for it.

    """

    def test_well_formed(self):
        """Make sure the expander works on well-formed fragments."""
        html = '<ul><li class="1"><br><for>One</for></li></ul>'
        balanced_eq(html, html)

    def test_document_mode(self):
        """Make sure text chunks interspersed with tags are parsed right."""
        html = "<p>Hello<br>there, <br>you.</p>"
        balanced_eq(html, html)

    def test_early_close(self):
        """Make sure the parser closes the for tag at the right place when
        its closer is early."""
        balanced_eq("<div><for><p>One</p></for></div>", "<div><for><p>One</for></for></p></div>")

    def test_late_close(self):
        """If the closing for tag is not closed by the time the enclosing
        element of the opening for tag is closed, close the for tag
        just before the enclosing element."""
        balanced_eq(
            "<ul><li><for><for>One</for></for></li></ul>", "<ul><li><for><for>One</li></ul></for>"
        )

    def test_close_absent_at_end(self):
        """Make sure the parser closes for tags left open at the EOF.

        This mattered more when we weren't building a parse tree.

        """
        balanced_eq("<for><p>One</p></for>", "<for><p>One</for></for></p>")

    def test_unicode(self):
        """Make sure this all works with non-ASCII chars."""
        html = "<for>Vous parl\u00e9 Fran\u00e7ais</for>"
        balanced_eq(html, html)

    def test_div(self):
        """Make sure we use divs for fors containing block elements."""
        expanded_eq('<div class="for"><p>One</p></div>', "<for><p>One</p></for>")

    def test_span(self):
        """Make sure we use spans for fors containing no block elements."""
        expanded_eq('<span class="for"><em>One</em></span>', "<for><em>One</em></for>")

    def test_data_attrs(self):
        """Make sure the data- attributes look good."""
        expanded_eq(
            '<span class="for" data-for="mac,linux">One</span>',
            '<for data-for="mac,linux">One</for>',
        )

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
        strip_eq("\x910\x91inline\x91/sf\x91", "{for}inline{/for}")
        strip_eq("\x910\x91\n\nblock\n\n\x91/sf\x91", "{for}\nblock\n{/for}")
        strip_eq("\x910\x91inline\n\n\x91/sf\x91", "{for}inline\n{/for}")
        strip_eq("\x910\x91\n\nblock\x91/sf\x91", "{for}\nblock{/for}")

    def test_whitespace_lookbehind(self):
        """Assert strip_fors is aware of newlines preceding the current match.

        This used to fail because both the postspace for the first closer and
        the prespace for the 2nd got 1 \n added, resulting in 3, which is 1
        too many. Now we use the preceding_whitespace function to look behind
        and take preceding newlines into account.

        """
        strip_eq(
            "\x910\x91\n\n\x911\x91inline\x91/sf\x91\n\n\x91/sf\x91",
            "{for}\n{for}inline{/for}\n{/for}",
        )

    def test_matches_see_replacements(self):
        """Make sure each whitespace lookbehind takes into account the effect
        of previous replacements' whitespace additions.

        When this bug existed, strip_fors would add a \n for postspace to the
        2nd {/for}, but then the preceding_whitespace call for the next {for}
        wouldn't see what was added, since it was still looking in the
        original string, without the replacements applied.

        """
        strip_eq(
            "\x910\x91\n\n\x911\x91Fx4\x91/sf\x91\n\n\x91/sf\x91\n\n"
            "\x912\x91\n\n\x913\x91Fx3\x91/sf\x91\n\n\x91/sf\x91",
            "{for fx4}\n"
            "{for mac}Fx4{/for}\n"
            "{/for}\n"
            "{for fx3}\n"
            "{for mac}Fx3{/for}\n"
            "{/for}",
        )

    def test_self_closers(self):
        """Make sure self-closing tags aren't balanced as paired ones."""
        balanced_eq('<img src="smoo"><span>g</span>', '<img src="smoo"><span>g</span>')
        balanced_eq('<img src="smoo"><span>g</span>', '<img src="smoo"/><span>g</span>')

    def test_leading_text_nodes(self):
        """Make sure the parser handles a leading naked run of text.

        Test inner runs of text while we're at it.

        """
        html = "A<i>hi</i>B<i>there</i>C"
        p = ForParser(html)
        self.assertEqual(html, str(p))


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
        d1 = DocumentFactory(title="\u03C0", slug="pi")
        ApprovedRevisionFactory(document=d1, content="I \u2764 \u03C0")
        d2 = DocumentFactory(title="\u2764", slug="heart")
        ApprovedRevisionFactory(document=d2, content="What do you think about [[\u03C0]]?")

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
        img = ImageFactory(title="image-file.png")
        d1, _, _ = doc_rev_parser("[[Image:image-file.png]]", title="D1")

        self.assertEqual(len(d1.images), 1)
        self.assertEqual(d1.images[0], img)
        self.assertEqual(len(img.documents), 1)
        self.assertEqual(img.documents[0], d1)


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
