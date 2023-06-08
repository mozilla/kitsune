from pathlib import Path
import subprocess
import textwrap

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


INDENT = " " * 3
CHECKMARK = "\u2713"


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

            # We need to use "sv_SE" instead of "sv" here because Pontoon
            # uses "sv-SE" for Swedish instead of "sv".
            # TODO: Remove this once Pontoon uses "sv" instead of "sv-SE"
            #       for Swedish.
            locale = "sv_SE" if locale == "sv" else locale

            for domain in ("django", "djangojs"):
                domain_pot = Path(f"locale/templates/LC_MESSAGES/{domain}.pot")
                if not domain_pot.is_file():
                    raise CommandError(f"unable to find {domain_pot}")
                domain_po = Path(f"locale/{locale}/LC_MESSAGES/{domain}.po")
                if not domain_po.parent.is_dir():
                    domain_po.parent.mkdir(parents=True)

                if not domain_po.is_file():
                    self.run(
                        f"initializing {domain_po}",
                        "msginit",
                        "--no-translator",
                        f"--locale={locale}",
                        f"--input={domain_pot}",
                        f"--output-file={domain_po}",
                        "--width=200",
                    )

                self.run(
                    f"updating {domain_po}",
                    "msgmerge",
                    "--update",
                    "--width=200",
                    "--backup=off",
                    domain_po,
                    domain_pot,
                )

    def run(self, description, *cmd_and_args):
        self.stdout.write(f"{description}...", ending="")
        try:
            subprocess.run(
                cmd_and_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as err:
            self.stdout.write(self.style.ERROR("x"))
            self.stdout.write(
                self.style.ERROR(textwrap.indent(f"error(s) while {description}:", INDENT))
            )
            self.stdout.write(self.style.ERROR(textwrap.indent(err.stdout, INDENT * 2)), ending="")
        else:
            self.stdout.write(self.style.SUCCESS(CHECKMARK))
