from babel.messages.frontend import CommandLineInterface
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Merge will merge the .pot files into the existing l10n files,
    which exist in locale (if you have the repo downloaded).

    """

    help = "Merges the .pot files into the existing l10n files."

    def handle(self, *args, **options):
        no_repo_locales = []
        for locale in settings.SUMO_LANGUAGES:
            if locale in ("en-US", "xx", "xx-testing", "templates"):
                continue
            try:
                CommandLineInterface().run(
                    [
                        "pybabel",
                        "update",
                        "-d",
                        "locale/",
                        "-l",
                        locale.replace("-", "_"),
                        "-D",
                        "django",
                        "-i",
                        "locale/templates/LC_MESSAGES/django.pot",
                    ]
                )
                CommandLineInterface().run(
                    [
                        "pybabel",
                        "update",
                        "-d",
                        "locale/",
                        "-l",
                        locale.replace("-", "_"),
                        "-D",
                        "djangojs",
                        "-i",
                        "locale/templates/LC_MESSAGES/djangojs.pot",
                    ]
                )
                self.stdout.write(f"Merge complete for {locale}.\n")
            except Exception as merge_error:
                self.stdout.write(f"Merge failed for {locale}.\n")
                self.stdout.write(f"Error: {merge_error}.\n")
                no_repo_locales.append(locale)
        if no_repo_locales:
            self.stdout.write(f"The following locales were unable to update: {no_repo_locales}.\n")
            self.stdout.write("Attempting to initialize them now.\n")
            for locale in no_repo_locales:
                try:
                    CommandLineInterface().run(
                        [
                            "pybabel",
                            "init",
                            "-d",
                            "locale/" + locale.repalce("-", "_"),
                            "-l",
                            locale.replace("-", "_"),
                            "-D",
                            "djangojs",
                            "-i",
                            "locale/templates/LC_MESSAGES/djangojs.pot",
                        ]
                    )
                    CommandLineInterface().run(
                        [
                            "pybabel",
                            "init",
                            "-d",
                            "locale/",
                            "-l",
                            locale.replace("-", "_"),
                            "-D",
                            "django",
                            "-i",
                            "locale/templates/LC_MESSAGES/django.pot",
                        ]
                    )
                except Exception as error:
                    self.stdout.write(f"Error: {error}.\n")
