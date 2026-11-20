from django.test import SimpleTestCase

from kitsune.llm.l10n.ui_labels.labels import find_label_uses


class LabelTests(SimpleTestCase):
    def test_finds_each_use_a_reader_can_see_and_where_its_text_is(self):
        content = (
            "= Windows =\n"
            "== Settings ==\n"
            "Open the menu.\n"
            "# Click {menu View}, then {button  OK }.\n"
            "= Mac =\n"
            "Open the app.\n"
            "<!-- == Old ==\n"
            "Click {menu Hidden}. -->\n"
            "Set {pref Begins with}<!-- a note --> here.\n"
        )
        uses = find_label_uses(content)

        self.assertEqual(
            [(use.kind, use.text) for use in uses],
            [("menu", "View"), ("button", "OK"), ("pref", "Begins with")],
        )
        self.assertEqual(
            [content[use.start : use.end] for use in uses], ["View", "OK", "Begins with"]
        )

    def test_says_what_is_not_a_label(self):
        for markup, expected in (
            ("{menu Settings}", "label"),
            ("{button Save As…}", "label"),
            ("{button 是}", "label"),
            ("{pref Begins with}", "label"),
            ("{pref debug}", "label"),
            ("{pref Advanced...}", "label"),
            ("{pref browser.tabs.warnOnClose}", "config"),
            ("{pref '''network.proxy.'''}", "config"),
            ("{pref devtools.}", "config"),
            ("{pref Done.}", "label"),
            ("{pref True}", "config"),
            ("{pref 3}", "config"),
            ("{menu browser.tabs.warnOnClose}", "label"),
            ("{button [[Image:Menu]]}", "markup"),
            ("{button Close <n> Tabs}", "markup"),
            ("{pref '''Dark'''}", "markup"),
            ("{button +}", "icon"),
            ("{pref *}", "icon"),
            ("{button K}", "key"),
            ("{button Ctrl}", "key"),
            ("{menu Settings > General}", "path"),
            ("{pref Tag | Is | Important}", "path"),
        ):
            with self.subTest(markup):
                [use] = find_label_uses(markup)
                self.assertEqual(use.category, expected)
