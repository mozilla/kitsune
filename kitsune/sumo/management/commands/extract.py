import subprocess

from django.core.management.base import BaseCommand
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
                ".",
            ]
        )
        # First run the Babel-based extraction on the JS-based Svelte and Nunjucks files.
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
                ".",
            ]
        )
        # Finally run the extraction on the JS files themselves. This will add to the
        # djangojs.pot file created by the previous command due to the "--join-existing"
        # option.
        subprocess.run(
            " ".join(
                [
                    "xgettext",
                    "--join-existing",
                    "--sort-by-file",
                    "--copyright-holder=Mozilla",
                    "--package-name=kitsune",
                    "--package-version=1.0",
                    "--msgid-bugs-address='https://github.com/mozilla-l10n/sumo-l10n/issues'",
                    "--output=locale/templates/LC_MESSAGES/djangojs.pot",
                    "--width=80",
                    "--add-comments='L10n,L10n:'",
                    "--keyword='_lazy'",
                    "--keyword='pgettext_lazy:1c,2'",
                    "--from-code=utf-8",
                    "kitsune/**/static/**/js/*.js",
                ]
            ),
            shell=True,
            check=True,
        )

        self.stdout.write(self.style.SUCCESS("extraction complete"))
