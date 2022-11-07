from pathlib import Path
import subprocess
import textwrap

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


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

            for domain in ("django", "djangojs"):

                domain_pot = Path(f"locale/templates/LC_MESSAGES/{domain}.pot")
                if not domain_pot.is_file():
                    raise CommandError(f"unable to find {domain_pot}")
                domain_po = Path(f"locale/{locale}/LC_MESSAGES/{domain}.po")
                if not domain_po.parent.is_dir():
                    domain_po.parent.mkdir(parents=True)

                if not domain_po.is_file():
                    self.run(
                        "msginit",
                        "--no-translator",
                        f"--locale={locale}",
                        f"--input={domain_pot}",
                        f"--output-file={domain_po}",
                        "--width=200",
                        on_success=f"initialized {domain_po}",
                        on_failure=f"error initializing {domain_po}",
                    )

                self.run(
                    "msgmerge",
                    "--update",
                    "--width=200",
                    "--backup=off",
                    domain_po,
                    domain_pot,
                    on_success=f"updated {domain_po}",
                    on_failure=f"error updating {domain_po}",
                )

    def run(self, *args, on_success=None, on_failure=None):
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if result.returncode == 0:
            if on_success:
                self.stdout.write(self.style.SUCCESS(on_success))
        else:
            if on_failure:
                self.stdout.write(self.style.ERROR(on_failure))
            self.stdout.write(self.style.ERROR(textwrap.indent(result.stdout, "   ")))
