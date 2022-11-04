from pathlib import Path

from babel import Locale, UnknownLocaleError
from babel.messages.frontend import CommandLineInterface
from django.conf import settings
from django.core.management.base import BaseCommand


def is_supported_for_init(locale):
    try:
        Locale.parse(locale)
    except UnknownLocaleError:
        return False
    return True


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

            if locale in ("en_US", "xx"):
                continue

            if Path(f"locale/{locale}").is_dir():
                command = [
                    "pybabel",
                    "update",
                    "--ignore-obsolete",
                ]
            elif not is_supported_for_init(locale):
                # NOTE: Babel only supports initializing locales included in the CLDR.
                self.stdout.write(
                    self.style.WARNING(f"WARNING: skipping locale {locale} (unsupported for init)")
                )
                continue
            else:
                command = ["pybabel", "init"]

            command.extend(
                (
                    "-d",
                    "locale/",
                    "-l",
                    locale,
                )
            )

            CommandLineInterface().run(
                command
                + [
                    "-D",
                    "django",
                    "-i",
                    "locale/templates/LC_MESSAGES/django.pot",
                ]
            )
            CommandLineInterface().run(
                command
                + [
                    "-D",
                    "djangojs",
                    "-i",
                    "locale/templates/LC_MESSAGES/djangojs.pot",
                ]
            )
