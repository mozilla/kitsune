import datetime
import glob
import re
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from babel.messages.frontend import CommandLineInterface


class Command(BaseCommand):
    """
    Allows you to extract strings for localization.
    Extract creates two .pot files - django.pot and djangojs.pot - that contain
    messages to merge into the existing l10n files.
    """

    help = "Extracts localizable strings from the codebase."

    def handle(self, *args, **options):
        CommandLineInterface().run(
            [
                "pybabel",
                "extract",
                "-F",
                "babel.cfg",
                "-o",
                "locale/templates/LC_MESSAGES/django.pot",
                "-k",
                "_lazy",
                "-k",
                "pgettext_lazy:1c,2",
                "-c",
                "L10n,L10n:",
                "-w",
                "80",
                "--version",
                "1.0",
                "--project=kitsune",
                "--copyright-holder=Mozilla",
                "--msgid-bugs-address=https://github.com/mozilla-l10n/sumo-l10n/issues",
                ".",
            ]
        )
        update_header_comments("locale/templates/LC_MESSAGES/django.pot")
        # First run the Babel-based extraction on the Svelte and Nunjucks files.
        CommandLineInterface().run(
            [
                "pybabel",
                "extract",
                "-F",
                "babeljs.cfg",
                "-o",
                "locale/templates/LC_MESSAGES/djangojs.pot",
                "-k",
                "_lazy",
                "-k",
                "pgettext_lazy:1c,2",
                "-c",
                "L10n,L10n:",
                "-w",
                "80",
                "--version",
                "1.0",
                "--project=kitsune",
                "--copyright-holder=Mozilla",
                "--msgid-bugs-address=https://github.com/mozilla-l10n/sumo-l10n/issues",
                ".",
            ]
        )
        # Finally run the extraction on the JS files themselves. This will add to the
        # existing djangojs.pot file created by the previous command (because we're
        # using the "--join-existing" option).
        # NOTE: This loop is for reporting purposes only. The "--verbose" option of
        #       "xgettext" doesn't seem to work.
        for fname in glob.glob("kitsune/**/static/**/js/*.js"):
            self.stdout.write(f"extracting messages from {fname}")
            try:
                subprocess.run(
                    [
                        "xgettext",
                        "--join-existing",
                        "--sort-by-file",
                        "--copyright-holder=Mozilla",
                        "--package-name=kitsune",
                        "--package-version=1.0",
                        "--msgid-bugs-address=https://github.com/mozilla-l10n/sumo-l10n/issues",
                        "--output=locale/templates/LC_MESSAGES/djangojs.pot",
                        "--width=80",
                        "--add-comments=L10n,L10n:",
                        "--keyword=_lazy",
                        "--keyword=pgettext_lazy:1c,2",
                        "--from-code=utf-8",
                        fname,
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
            except subprocess.CalledProcessError as err:
                raise CommandError(err.output)

        update_header_comments("locale/templates/LC_MESSAGES/djangojs.pot")

        self.stdout.write(self.style.SUCCESS("extraction complete"))


def update_header_comments(filename):
    """Given a POT filename, adjust some of the header comments if necessary."""
    current_year = datetime.datetime.now().year
    replacements = [
        (
            re.compile(r"^# SOME DESCRIPTIVE TITLE.$", flags=re.MULTILINE),
            "# Translations template for kitsune.",
        ),
        (
            re.compile(r"^# Copyright \(C\) YEAR Mozilla$", flags=re.MULTILINE),
            f"# Copyright (C) {current_year} Mozilla",
        ),
        (
            re.compile(
                (
                    r"^# This file is distributed under the same license as the "
                    r"kitsune (package|project).$"
                ),
                flags=re.MULTILINE,
            ),
            (
                "# This file is distributed under the license specified at "
                "https://github.com/mozilla-l10n/sumo-l10n."
            ),
        ),
        (
            re.compile(r"^# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.$", flags=re.MULTILINE),
            f"# FIRST AUTHOR <EMAIL@ADDRESS>, {current_year}.",
        ),
    ]
    pot_file = Path(filename)
    text = pot_file.read_text()
    for regex, replacement in replacements:
        text = regex.sub(replacement, text, count=1)
    pot_file.write_text(text)
