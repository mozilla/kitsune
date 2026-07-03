import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from django.utils import timezone

from kitsune.sumo.management.commands.extract import Command


@contextmanager
def chdir(path):
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


class ExtractCommandTests(SimpleTestCase):
    """Test that the extract command works and applies the correct resource comment."""
    def test_extract_writes_template_files_without_author_placeholder(self):
        with TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "babel.cfg").write_text("[python: **.py]\n")
            (root / "babeljs.cfg").write_text("[javascript: **.js]\n")
            (root / "strings.py").write_text('_lazy("Python string")\n')
            (root / "strings.js").write_text('_lazy("JavaScript string");\n')
            (root / "locale/templates/LC_MESSAGES").mkdir(parents=True)

            with chdir(root):
                Command().handle()

            current_year = timezone.now().year
            for filename in ("django.pot", "djangojs.pot"):
                path = root / "locale/templates/LC_MESSAGES" / filename
                text = path.read_text()

                self.assertIn("# Translations template for kitsune.", text)
                self.assertIn(f"# Copyright (C) {current_year} Mozilla", text)
                self.assertIn("# This file is distributed under the license specified at", text)
                self.assertIn("https://github.com/mozilla-l10n/sumo-l10n.", text)
                self.assertNotIn("FIRST AUTHOR", text)

            django_pot = root / "locale/templates/LC_MESSAGES/django.pot"
            djangojs_pot = root / "locale/templates/LC_MESSAGES/djangojs.pot"
            self.assertIn('msgid "Python string"', django_pot.read_text())
            self.assertIn('msgid "JavaScript string"', djangojs_pot.read_text())
