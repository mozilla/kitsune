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

        self.stdout.write("Extraction complete.\n")
