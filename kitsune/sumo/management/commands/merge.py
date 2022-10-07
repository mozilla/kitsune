from pathlib import Path

from babel.messages.frontend import CommandLineInterface
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Merge will update the .po files for all locales based on the .pot files, or
    if the .po files don't yet exist for a locale, initialize them. It assumes that
    you've cloned the https://github.com/mozilla-l10n/sumo-l10n repo into the "locale"
    sub-directory.
    """

    help = "Updates or initializes the .po files for all locales."

    def handle(self, *args, **options):
        for locale in settings.SUMO_LANGUAGES:
            locale = locale.replace("-", "_")
            if locale in ("en_US", "tn", "xx"):
                # NOTE: The "tn" locale is not supported by the CLDR,
                #       which Babel uses, and "xx" is a test locale.
                continue
            sub_cmd = "update" if Path(f"locale/{locale}").is_dir() else "init"
            CommandLineInterface().run(
                [
                    "pybabel",
                    sub_cmd,
                    "-d",
                    "locale/",
                    "-l",
                    locale,
                    "-D",
                    "django",
                    "-i",
                    "locale/templates/LC_MESSAGES/django.pot",
                ]
            )
            CommandLineInterface().run(
                [
                    "pybabel",
                    sub_cmd,
                    "-d",
                    "locale/",
                    "-l",
                    locale,
                    "-D",
                    "djangojs",
                    "-i",
                    "locale/templates/LC_MESSAGES/djangojs.pot",
                ]
            )
