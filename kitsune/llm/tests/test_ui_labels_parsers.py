from django.test import SimpleTestCase

from kitsune.llm.l10n.ui_labels.strings.parsers.fluent import FluentFiles
from kitsune.llm.l10n.ui_labels.strings.parsers.standalone import parse
from kitsune.llm.l10n.ui_labels.strings.parsers.ui_string import UIString


class FluentTests(SimpleTestCase):
    def strings(self, **files):
        fluent = FluentFiles()
        for path, text in files.items():
            fluent.add(path, text)
        return {string.id: string.text for string in fluent.strings()}

    def test_brand_terms_use_the_case_the_string_asks_for(self):
        strings = self.strings(
            brand="""
-brand-short-name =
    { $case ->
        [gen] Thunderbirda
       *[nom] Thunderbird
    }
""",
            menu="""
about = O programie { -brand-short-name }
settings = Ustawienia { -brand-short-name(case: "gen") }
""",
        )
        self.assertEqual(
            strings,
            {"menu:about": "O programie Thunderbird", "menu:settings": "Ustawienia Thunderbirda"},
        )

    def test_one_entry_per_platform(self):
        strings = self.strings(
            prefs="""
open =
    { PLATFORM() ->
        [macos] Preferences
       *[other] Options
    }
shortcut =
    { PLATFORM() ->
        [macos] Cmd
       *[other] Ctrl
    } + { open }
"""
        )
        self.assertEqual(
            strings,
            {
                "prefs:open[macos]": "Preferences",
                "prefs:open[other]": "Options",
                "prefs:shortcut[macos]": "Cmd + Preferences",
                "prefs:shortcut[other]": "Ctrl + Options",
            },
        )

    def test_attributes_references_and_comments(self):
        fluent = FluentFiles()
        fluent.add(
            "menu",
            """
# Shown in the menu bar.
menu-view =
    .label = View
    .accesskey = V
    .buttonAccessKey = W
toolbar-view = { menu-view.label } toolbars
recent-no-accesskey =
    .label = Recent
""",
        )
        self.assertEqual(
            list(fluent.strings()),
            [
                UIString("menu:menu-view.label", "View", "Shown in the menu bar."),
                UIString("menu:toolbar-view", "View toolbars"),
                UIString("menu:recent-no-accesskey.label", "Recent"),
            ],
        )

    def test_the_same_name_in_two_files_keeps_both(self):
        strings = self.strings(robots="page-title = Robots", support="page-title = Support")
        self.assertEqual(strings, {"robots:page-title": "Robots", "support:page-title": "Support"})

    def test_text_only_known_when_the_product_runs_is_left_out(self):
        strings = self.strings(
            tabs="""
close = Close { $count } tabs
plural =
    { $count ->
        [one] Close tab
       *[other] Close tabs
    }
missing = Open { -no-such-term }
loop = { loop }
done = Done
"""
        )
        self.assertEqual(strings, {"tabs:done": "Done"})


class ParserTests(SimpleTestCase):
    def parse(self, path, text, english=False):
        return list(parse(path, text.encode(), "Firefox", english))

    def test_properties(self):
        strings = self.parse(
            "x.properties",
            "# The save button\n"
            "save.label = Enregistrer \\\r\n   sous\\u2026\n"
            "save.accesskey = E\n"
            "saveAccessKey = E\n"
            "empty =\n"
            "invited = %S a accepté\n"
            "about = À propos\n",
        )
        self.assertEqual(
            strings,
            [
                UIString("x.properties:save.label", "Enregistrer sous…", "The save button"),
                UIString("x.properties:about", "À propos"),
            ],
        )

    def test_dtd(self):
        strings = self.parse(
            "x.dtd",
            '<!ENTITY quit.label "Quitter &brandShortName;">\n'
            '<!ENTITY quit.accessKey "Q">\n'
            '<!ENTITY empty.label "">\n'
            '<!-- <!ENTITY old.label "Ancien"> -->\n'
            "<!ENTITY help.label 'Aide'>\n",
        )
        self.assertEqual(
            strings,
            [
                UIString("x.dtd:quit.label", "Quitter Firefox"),
                UIString("x.dtd:help.label", "Aide"),
            ],
        )

    def test_android(self):
        strings = self.parse(
            "strings.xml",
            """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE resources [<!ENTITY secret "expanded">]>
<resources xmlns:xliff="urn:oasis:names:tc:xliff:document:1.2">
  <!-- Menu item -->
  <string name="save">Zachowaj
      w\\u00a0kolekcji</string>
  <!-- About tabs -->
  <plurals name="tabs"><item quantity="one">%d karta</item></plurals>
  <string name="about">"O\\'programie <xliff:g id="app">%1$s</xliff:g>"</string>
  <string name="moved">Z %1$s do %2$s</string>
  <string name="count">Karty: %1$d</string>
  <string name="full">100%% &secret;</string>
</resources>""",
        )
        self.assertEqual(
            strings,
            [
                UIString("strings.xml:save", "Zachowaj w\u00a0kolekcji", "Menu item"),
                UIString("strings.xml:about", "O'programie Firefox"),
                UIString("strings.xml:full", "100% &secret;"),
            ],
        )

    def test_xliff_reads_english_or_the_translation(self):
        xliff = """<?xml version="1.0" encoding="utf-8"?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
  <file original="Settings.strings">
    <body>
      <trans-unit id="Clear"><source>Clear Private Data</source>
        <target>Effacer <g>mes</g> traces</target><note>A button</note></trans-unit>
      <trans-unit id="New"><source>Open %@</source></trans-unit>
    </body>
  </file>
</xliff>"""
        self.assertEqual(
            self.parse("x.xliff", xliff),
            [UIString("x.xliff:Settings.strings:Clear", "Effacer mes traces", "A button")],
        )
        self.assertEqual(
            self.parse("x.xliff", xliff, english=True),
            [
                UIString("x.xliff:Settings.strings:Clear", "Clear Private Data", "A button"),
                UIString("x.xliff:Settings.strings:New", "Open Firefox"),
            ],
        )

    def test_gettext_reads_english_or_the_translation(self):
        po = (
            'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n'
            '"Plural-Forms: nplurals=INTEGER; plural=EXPRESSION;\\n"\n\n'
            '#. A button\nmsgid "Submit"\nmsgstr "Envoyer"\n\n'
            'msgctxt "verb"\nmsgid "Review"\nmsgstr ""\n\n'
            '#, fuzzy\nmsgid "Preview"\nmsgstr "Aperçu"\n'
        )
        self.assertEqual(
            self.parse("amo.po", po), [UIString("amo.po:Submit", "Envoyer", "A button")]
        )
        self.assertEqual(
            self.parse("amo.pot", po, english=True),
            [
                UIString("amo.po:Submit", "Submit", "A button"),
                UIString("amo.po:verb\x04Review", "Review"),
            ],
        )
