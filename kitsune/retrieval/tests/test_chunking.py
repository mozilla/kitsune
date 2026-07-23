from django.test import SimpleTestCase

from kitsune.retrieval.chunking import (
    MAX_TOKENS,
    Chunk,
    chunk,
    chunk_kb,
    count_tokens,
    parse_data_for,
)
from kitsune.wiki.parser import WikiParser


class ChunkKBTests(SimpleTestCase):
    def test_single_paragraph_becomes_one_unconditional_chunk(self):
        chunks = chunk_kb(
            "<p>Reset your password from the account menu.</p>",
            title="Reset your password",
        )

        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertIsInstance(result, Chunk)
        self.assertEqual(result.position, 0)
        self.assertIn("Reset your password from the account menu.", result.text)
        self.assertEqual(result.heading_path, "Reset your password")
        self.assertEqual(result.applies_to, frozenset())

    def test_splits_into_intro_and_heading_sections(self):
        html = (
            "<p>Intro text.</p>"
            "<h2>First section</h2><p>First body.</p>"
            "<h2>Second section</h2><p>Second body.</p>"
        )
        chunks = chunk_kb(html, title="My Article")

        self.assertEqual(len(chunks), 3)
        self.assertEqual([c.position for c in chunks], [0, 1, 2])
        self.assertEqual(chunks[0].heading_path, "My Article")
        self.assertIn("Intro text.", chunks[0].text)
        self.assertEqual(chunks[1].heading_path, "My Article > First section")
        self.assertIn("First body.", chunks[1].text)
        self.assertEqual(chunks[2].heading_path, "My Article > Second section")
        self.assertIn("Second body.", chunks[2].text)

    def test_nested_subsection_builds_hierarchical_heading_path(self):
        html = "<h2>Section</h2><p>Body.</p><h3>Subsection</h3><p>Sub body.</p>"
        chunks = chunk_kb(html, title="Guide")

        paths = [c.heading_path for c in chunks]
        self.assertIn("Guide > Section", paths)
        self.assertIn("Guide > Section > Subsection", paths)


class ChunkDispatchTests(SimpleTestCase):
    def test_kb_content_type_routes_to_chunk_kb(self):
        html = "<p>Clear your cache from settings.</p>"
        self.assertEqual(
            chunk("kb", html, title="Clear cache"),
            chunk_kb(html, title="Clear cache"),
        )

    def test_unknown_content_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            chunk("forum", "<p>x</p>", title="x")


class ParseDataForTests(SimpleTestCase):
    def test_splits_comma_separated_tokens(self):
        self.assertEqual(parse_data_for("win, mac"), frozenset({"win", "mac"}))

    def test_preserves_negation_as_single_token(self):
        self.assertEqual(parse_data_for("not fx63"), frozenset({"not fx63"}))

    def test_empty_value_is_unconditional(self):
        self.assertEqual(parse_data_for(""), frozenset())


class ChunkForScopeTests(SimpleTestCase):
    def test_for_blocks_produce_separately_scoped_chunks(self):
        html = (
            "<p>Common intro.</p>"
            '<div class="for" data-for="win"><p>Windows steps.</p></div>'
            '<div class="for" data-for="android"><p>Android steps.</p></div>'
        )
        chunks = chunk_kb(html, title="Clear cache")

        expected = {
            "Common intro.": frozenset(),
            "Windows steps.": frozenset({"win"}),
            "Android steps.": frozenset({"android"}),
        }
        for content, applies_to in expected.items():
            matching = [c for c in chunks if content in c.text]
            self.assertEqual(len(matching), 1, content)
            self.assertEqual(matching[0].applies_to, applies_to)

        for c in chunks:
            self.assertFalse("Windows steps." in c.text and "Android steps." in c.text)

    def test_nested_for_intersects_scope(self):
        html = (
            '<div class="for" data-for="win">'
            '<div class="for" data-for="fx63"><p>Win and fx63.</p></div>'
            "</div>"
        )
        chunks = chunk_kb(html, title="Guide")

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].applies_to, frozenset({"win", "fx63"}))

    def test_for_div_with_nested_heading_scopes_and_keeps_path(self):
        html = '<div class="for" data-for="win"><h2>Scoped</h2><p>Windows only.</p></div>'
        chunks = chunk_kb(html, title="Guide")

        section = next(c for c in chunks if "Windows only." in c.text)
        self.assertEqual(section.applies_to, frozenset({"win"}))
        self.assertEqual(section.heading_path, "Guide > Scoped")

    def test_heading_inside_for_block_does_not_leak_to_later_content(self):
        html = (
            "<h1>Guide</h1>"
            '<div class="for" data-for="win"><h2>Windows</h2><p>Win step.</p></div>'
            "<p>Common note.</p>"
        )
        chunks = chunk_kb(html, title="Article")

        common = next(c for c in chunks if "Common note." in c.text)
        self.assertEqual(common.heading_path, "Article > Guide")
        self.assertEqual(common.applies_to, frozenset())

    def test_conditional_same_level_heading_does_not_shadow_outer(self):
        html = (
            "<h2>Common</h2>"
            '<div class="for" data-for="win"><h2>Windows</h2><p>Win step.</p></div>'
            "<p>After.</p>"
        )
        chunks = chunk_kb(html, title="Guide")

        after = next(c for c in chunks if "After." in c.text)
        self.assertEqual(after.heading_path, "Guide > Common")
        self.assertEqual(after.applies_to, frozenset())

    def test_span_for_wrapper_headings_update_the_heading_stack(self):
        # expand_fors emits <span class="for"> around block content too; its headings must count
        html = (
            "<h2>PDF Viewer</h2><p>PDF stuff.</p>"
            '<span class="for" data-for="win"><h2>Miscellaneous</h2><p>Misc stuff.</p></span>'
        )
        chunks = chunk_kb(html, title="Shortcuts")

        misc = next(c for c in chunks if "Misc stuff." in c.text)
        self.assertEqual(misc.heading_path, "Shortcuts > Miscellaneous")
        self.assertEqual(misc.applies_to, frozenset({"win"}))
        self.assertNotIn("MiscellaneousMisc", misc.text)

        pdf = next(c for c in chunks if "PDF stuff." in c.text)
        self.assertEqual(pdf.heading_path, "Shortcuts > PDF Viewer")


class ChunkInlineForProjectionTests(SimpleTestCase):
    def test_inline_scopes_emit_faithful_signature_projections_and_base(self):
        html = (
            "<p>Choose "
            '<span class="for" data-for="win">Windows</span>'
            " or "
            '<span class="for" data-for="mac">Mac</span>'
            ".</p>"
        )

        chunks = chunk_kb(html, title="Guide")
        by_scope = {chunk.applies_to: chunk for chunk in chunks}

        self.assertEqual(set(by_scope), {frozenset(), frozenset({"win"}), frozenset({"mac"})})
        self.assertEqual(by_scope[frozenset()].text, "Guide\nChoose or .")
        self.assertEqual(by_scope[frozenset({"win"})].text, "Guide\nChoose Windows or .")
        self.assertEqual(by_scope[frozenset({"mac"})].text, "Guide\nChoose or Mac.")

    def test_distinct_signatures_are_not_combined_into_reader_cartesian_product(self):
        html = (
            "<p>Shared "
            '<span class="for" data-for="win">Windows</span>'
            " middle "
            '<span class="for" data-for="fx100">Firefox 100</span>'
            " end.</p>"
        )

        chunks = chunk_kb(html, title="Guide")

        self.assertEqual(
            {chunk.applies_to for chunk in chunks},
            {frozenset(), frozenset({"win"}), frozenset({"fx100"})},
        )
        self.assertFalse(any(chunk.applies_to == frozenset({"win", "fx100"}) for chunk in chunks))

    def test_nested_inline_scope_inherits_its_parent_context(self):
        html = (
            "<p>Shared "
            '<span class="for" data-for="win">Windows '
            '<span class="for" data-for="fx100">Firefox 100</span>'
            "</span>.</p>"
        )

        chunks = chunk_kb(html, title="Guide")
        by_scope = {chunk.applies_to: chunk for chunk in chunks}

        self.assertEqual(
            set(by_scope),
            {frozenset(), frozenset({"win"}), frozenset({"win", "fx100"})},
        )
        self.assertIn("Windows", by_scope[frozenset({"win"})].text)
        self.assertNotIn("Firefox 100", by_scope[frozenset({"win"})].text)
        nested = by_scope[frozenset({"win", "fx100"})]
        self.assertIn("Shared Windows Firefox 100.", nested.text)
        self.assertEqual(
            nested.scope,
            (frozenset({"win"}), frozenset({"fx100"})),
        )

    def test_comma_clause_and_nested_clauses_remain_distinct(self):
        html = (
            "<p>"
            '<span class="for" data-for="win,mac">Either desktop.</span> '
            '<span class="for" data-for="win">Windows '
            '<span class="for" data-for="mac">and Mac together.</span>'
            "</span>"
            "</p>"
        )

        chunks = chunk_kb(html, title="Guide")
        comma_scope = (frozenset({"win", "mac"}),)
        nested_scope = (frozenset({"win"}), frozenset({"mac"}))
        by_scope = {chunk.scope: chunk for chunk in chunks}

        self.assertIn(comma_scope, by_scope)
        self.assertIn(nested_scope, by_scope)
        self.assertEqual(by_scope[comma_scope].text, "Guide\nEither desktop.")
        self.assertEqual(by_scope[nested_scope].text, "Guide\nWindows and Mac together.")
        self.assertEqual(
            by_scope[comma_scope].applies_to,
            by_scope[nested_scope].applies_to,
        )

    def test_nested_platform_detail_keeps_the_instruction_it_qualifies(self):
        html = (
            '<div class="for" data-for="win"><ul><li>'
            "View the Windows Task Manager Performance tab"
            '<span class="for" data-for="win8,win10"> '
            '(click "More details" to show all tabs)</span>.'
            "</li></ul></div>"
        )

        chunks = chunk_kb(html, title="Troubleshooting")
        nested = next(chunk for chunk in chunks if "More details" in chunk.text)

        self.assertEqual(
            nested.scope,
            (frozenset({"win"}), frozenset({"win8", "win10"})),
        )
        self.assertIn("View the Windows Task Manager Performance tab", nested.text)
        self.assertIn('(click "More details" to show all tabs).', nested.text)

    def test_repeated_nested_clause_does_not_create_a_duplicate_variant(self):
        html = (
            "<p>"
            '<span class="for" data-for="win">Windows '
            '<span class="for" data-for="win">settings</span>.'
            "</span>"
            "</p>"
        )

        chunks = chunk_kb(html, title="Guide")

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].scope, (frozenset({"win"}),))
        self.assertEqual(chunks[0].text, "Guide\nWindows settings.")

    def test_adjacent_inline_blocks_merge_within_each_signature_projection(self):
        html = (
            '<p>Open <span class="for" data-for="win">Options</span>'
            '<span class="for" data-for="mac">Preferences</span>.</p>'
            '<p>Select <span class="for" data-for="win">General</span>'
            '<span class="for" data-for="mac">Settings</span>.</p>'
        )

        chunks = chunk_kb(html, title="Guide")
        by_scope = {chunk.applies_to: chunk for chunk in chunks}

        self.assertEqual(len(chunks), 3)
        self.assertIn("Open Options.", by_scope[frozenset({"win"})].text)
        self.assertIn("Select General.", by_scope[frozenset({"win"})].text)
        self.assertIn("Open Preferences.", by_scope[frozenset({"mac"})].text)
        self.assertIn("Select Settings.", by_scope[frozenset({"mac"})].text)

    def test_inline_scopes_in_heading_project_heading_path_for_common_body(self):
        html = (
            "<h2>Open "
            '<span class="for" data-for="win">Options</span>'
            '<span class="for" data-for="mac">Preferences</span>'
            "</h2><p>Change the setting.</p>"
        )

        chunks = chunk_kb(html, title="Guide")
        paths = {chunk.applies_to: chunk.heading_path for chunk in chunks}

        self.assertEqual(paths[frozenset()], "Guide > Open")
        self.assertEqual(paths[frozenset({"win"})], "Guide > Open Options")
        self.assertEqual(paths[frozenset({"mac"})], "Guide > Open Preferences")

    def test_inline_scopes_inside_list_items_keep_structure(self):
        html = (
            "<ul><li>Click "
            '<span class="for" data-for="win">Options</span>'
            '<span class="for" data-for="mac">Preferences</span>'
            ".</li><li>Restart Firefox.</li></ul>"
        )

        chunks = chunk_kb(html, title="Guide")
        by_scope = {chunk.applies_to: chunk for chunk in chunks}

        self.assertIn("Click Options.", by_scope[frozenset({"win"})].text)
        self.assertIn("Click Preferences.", by_scope[frozenset({"mac"})].text)
        self.assertIn("Restart Firefox.", by_scope[frozenset()].text)

    def test_table_of_only_conditional_cells_has_no_base_chunk_and_no_dangling_separators(self):
        html = (
            "<table><tr>"
            '<td><span class="for" data-for="win">Windows</span></td>'
            '<td><span class="for" data-for="mac">Mac</span></td>'
            "</tr></table>"
        )
        chunks = chunk_kb(html, title="Guide")
        by_scope = {c.applies_to: c for c in chunks}

        self.assertEqual(set(by_scope), {frozenset({"win"}), frozenset({"mac"})})
        self.assertEqual(by_scope[frozenset({"win"})].text, "Guide\nWindows")
        self.assertEqual(by_scope[frozenset({"mac"})].text, "Guide\nMac")

    def test_pretty_printed_conditional_table_has_no_dangling_separators(self):
        # whitespace between/around cells must not flush the pending cell separator
        html = (
            "<table><tr>"
            '<td>\n<span class="for" data-for="win">Windows</span>\n</td>'
            '<td>\n<span class="for" data-for="mac">Mac</span>\n</td>'
            "</tr></table>"
        )
        chunks = chunk_kb(html, title="Guide")
        by_scope = {c.applies_to: c for c in chunks}

        self.assertEqual(set(by_scope), {frozenset({"win"}), frozenset({"mac"})})
        self.assertEqual(by_scope[frozenset({"win"})].text, "Guide\nWindows")
        self.assertEqual(by_scope[frozenset({"mac"})].text, "Guide\nMac")

    def test_wiki_parser_output_preserves_inline_scope_boundaries(self):
        stored_html = WikiParser().parse("Choose {for win}Windows{/for} or {for mac}Mac{/for}.")

        chunks = chunk_kb(stored_html, title="Guide")

        self.assertEqual(
            {chunk.applies_to for chunk in chunks},
            {frozenset(), frozenset({"win"}), frozenset({"mac"})},
        )

    def test_wiki_parser_output_preserves_nested_clause_paths(self):
        stored_html = WikiParser().parse(
            '{for win}View the Performance tab {for win8,win10}(click "More details"){/for}.{/for}'
        )

        chunks = chunk_kb(stored_html, title="Guide")
        nested = next(chunk for chunk in chunks if "More details" in chunk.text)

        self.assertEqual(
            nested.scope,
            (frozenset({"win"}), frozenset({"win8", "win10"})),
        )
        self.assertIn('View the Performance tab (click "More details").', nested.text)

    def test_wiki_parser_output_preserves_block_scope_boundaries(self):
        stored_html = WikiParser().parse(
            "Common intro.\n\n{for win}\n* Windows step.\n{/for}\n\nCommon ending."
        )

        chunks = chunk_kb(stored_html, title="Guide")

        windows = next(chunk for chunk in chunks if "Windows step." in chunk.text)
        common = [chunk for chunk in chunks if "Common" in chunk.text]
        self.assertEqual(windows.applies_to, frozenset({"win"}))
        self.assertTrue(common)
        self.assertTrue(all(chunk.applies_to == frozenset() for chunk in common))


class ChunkWrapperTests(SimpleTestCase):
    def test_heading_inside_plain_wrapper_div_keeps_path(self):
        html = "<div><h2>Section</h2><p>Body text.</p></div>"
        chunks = chunk_kb(html, title="Guide")

        section = next(c for c in chunks if "Body text." in c.text)
        self.assertEqual(section.heading_path, "Guide > Section")

    def test_heading_inside_section_wrapper_keeps_path(self):
        html = "<section><h2>Part</h2><p>Section body.</p></section>"
        chunks = chunk_kb(html, title="Guide")

        section = next(c for c in chunks if "Section body." in c.text)
        self.assertEqual(section.heading_path, "Guide > Part")


class ChunkElementTests(SimpleTestCase):
    def test_table_is_linearized_to_readable_text(self):
        html = (
            "<table>"
            "<tr><td>OS</td><td>Shortcut</td></tr>"
            "<tr><td>Windows</td><td>Ctrl+Shift+Del</td></tr>"
            "</table>"
        )
        text = chunk_kb(html, title="Shortcuts")[0].text
        self.assertIn("OS", text)
        self.assertIn("Ctrl+Shift+Del", text)
        self.assertNotIn("OSShortcut", text)
        self.assertNotIn("WindowsCtrl", text)

    def test_ordered_list_items_are_separated_and_ordered(self):
        html = "<ol><li>First step.</li><li>Second step.</li></ol>"
        text = chunk_kb(html, title="Steps")[0].text
        self.assertIn("First step.", text)
        self.assertIn("Second step.", text)
        self.assertLess(text.index("First step."), text.index("Second step."))
        self.assertNotIn("step.Second", text)

    def test_whitespace_runs_are_normalized(self):
        text = chunk_kb("<p>Too    many\n\n   spaces.</p>", title="WS")[0].text
        self.assertIn("Too many spaces.", text)
        self.assertNotIn("Too    many", text)

    def test_space_before_punctuation_is_preserved(self):
        # locale content (e.g. French) legitimately spaces punctuation; keep it faithful
        text = chunk_kb("<p>Attention : important !</p>", title="Guide")[0].text
        self.assertIn("Attention : important !", text)

    def test_pre_block_preserves_internal_whitespace(self):
        text = chunk_kb("<pre>line one\n    indented</pre>", title="Code")[0].text
        self.assertIn("line one\n    indented", text)


class ChunkSizeTests(SimpleTestCase):
    def test_count_tokens_zero_for_empty(self):
        self.assertEqual(count_tokens(""), 0)

    def test_count_tokens_grows_with_length(self):
        self.assertLess(
            count_tokens("short"),
            count_tokens("a considerably longer stretch of text here indeed"),
        )

    def test_short_section_stays_single_chunk(self):
        chunks = chunk_kb("<p>A short paragraph.</p>", title="Small")
        self.assertEqual(len(chunks), 1)

    def test_long_section_splits_into_overlapping_chunks_within_limit(self):
        sentences = [f"Step {i} explains a distinct part of the procedure." for i in range(400)]
        chunks = chunk_kb("<p>" + " ".join(sentences) + "</p>", title="Big")

        self.assertGreater(len(chunks), 1)
        for chunk_obj in chunks:
            self.assertLessEqual(count_tokens(chunk_obj.text), MAX_TOKENS)
        self.assertTrue(any(s in chunks[0].text and s in chunks[1].text for s in sentences))

    def test_punctuation_free_passage_splits_within_limit(self):
        passage = " ".join(["word"] * 4000)
        chunks = chunk_kb(f"<p>{passage}</p>", title="Big")

        self.assertGreater(len(chunks), 1)
        for chunk_obj in chunks:
            self.assertLessEqual(count_tokens(chunk_obj.text), MAX_TOKENS)

    def test_unbroken_run_is_hard_split_within_limit(self):
        chunks = chunk_kb("<pre>" + "x" * 5000 + "</pre>", title="Blob")

        self.assertGreater(len(chunks), 1)
        for chunk_obj in chunks:
            self.assertLessEqual(count_tokens(chunk_obj.text), MAX_TOKENS)

    def test_oversized_pre_block_preserves_line_breaks(self):
        code = "\n".join(f"    indented line {i} of code" for i in range(400))
        chunks = chunk_kb(f"<pre>{code}</pre>", title="Code")

        self.assertGreater(len(chunks), 1)
        for chunk_obj in chunks:
            self.assertLessEqual(count_tokens(chunk_obj.text), MAX_TOKENS)
        self.assertTrue(any(chunk_obj.text.count("\n") > 1 for chunk_obj in chunks))

    def test_hard_split_chunks_overlap(self):
        passage = " ".join(f"word{i}" for i in range(4000))
        chunks = chunk_kb(f"<p>{passage}</p>", title="Big")

        self.assertGreater(len(chunks), 1)
        overlap = (set(chunks[0].text.split()) & set(chunks[1].text.split())) - {"Big"}
        self.assertTrue(overlap, "consecutive hard-split chunks should share overlap words")


class ChunkAssemblyTests(SimpleTestCase):
    def test_chunk_text_is_prefixed_with_heading_path(self):
        html = "<h2>Clear cache</h2><p>Open the menu.</p>"
        chunks = chunk_kb(html, title="Firefox")

        section = next(c for c in chunks if "Open the menu." in c.text)
        self.assertTrue(section.text.startswith("Firefox > Clear cache"))
        self.assertEqual(section.heading_path, "Firefox > Clear cache")

    def test_end_to_end_realistic_article(self):
        details = " ".join(f"Detail sentence {i}." for i in range(400))
        html = (
            "<p>Intro paragraph.</p>"
            "<h2>Install</h2>"
            '<div class="for" data-for="win"><p>Windows install steps.</p></div>'
            '<div class="for" data-for="mac"><p>Mac install steps.</p></div>'
            "<h2>Details</h2>"
            f"<p>{details}</p>"
        )
        chunks = chunk_kb(html, title="Setup")

        self.assertEqual([c.position for c in chunks], list(range(len(chunks))))
        for c in chunks:
            self.assertLessEqual(count_tokens(c.text), MAX_TOKENS)
            self.assertTrue(c.text.startswith("Setup"))
            self.assertFalse("Windows install steps." in c.text and "Mac install steps." in c.text)

        win = next(c for c in chunks if "Windows install steps." in c.text)
        mac = next(c for c in chunks if "Mac install steps." in c.text)
        self.assertEqual(win.applies_to, frozenset({"win"}))
        self.assertEqual(mac.applies_to, frozenset({"mac"}))
        self.assertEqual(win.heading_path, "Setup > Install")

        detail_chunks = [c for c in chunks if "Detail sentence" in c.text]
        self.assertGreater(len(detail_chunks), 1)
        for c in detail_chunks:
            self.assertEqual(c.heading_path, "Setup > Details")
            self.assertEqual(c.applies_to, frozenset())
