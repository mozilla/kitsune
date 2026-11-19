from django.test import SimpleTestCase

from kitsune.llm.l10n.ui_labels.text import loosen, normalize


class TextTests(SimpleTestCase):
    def test_normalize(self):
        for text, expected in (
            ("Don’t  ask\u00a0again", "Don't ask again"),
            ("Save As...", "Save As…"),
            ("Privacy &amp; Security", "Privacy & Security"),
            ("“Help”", '"Help"'),
            ("Cafe\u0301", "Café"),
        ):
            with self.subTest(text):
                self.assertEqual(normalize(text), expected)

    def test_loosen(self):
        for text, expected in (
            ("Save As…", "save as"),
            ("AI Controls", "ai controls"),
            ("Name:", "name"),
            ("Done.", "done"),
            ("about:config", "about:config"),
            ("…", "…"),
        ):
            with self.subTest(text):
                self.assertEqual(loosen(text), expected)
