from django.core.management.base import BaseCommand
from django.conf import settings
from wagtail.models import Page, Locale
from wagtail_localize.models import Translation, TranslationSource


class Command(BaseCommand):
    help = "Enables all the locales and syncs the locale trees to match English."

    def handle(self, *args, **options):
        SUMO_LANGUAGES = settings.SUMO_LANGUAGES

        # Enable all locales
        for lang_code in SUMO_LANGUAGES:
            locale, created = Locale.objects.get_or_create(language_code=lang_code)
            if created:
                self.stdout.write(f"Locale {lang_code} created.")
            else:
                self.stdout.write(f"Locale {lang_code} already exists.")

        # Get the English locale
        english_locale = Locale.objects.get(language_code="en-us")

        # For each locale (excluding English), sync the pages
        for locale in Locale.objects.exclude(language_code="en-us"):
            self.stdout.write(f"Syncing pages for locale {locale.language_code}...")

            # For each page in English, create or update translation in target locale
            english_pages = Page.objects.filter(locale=english_locale).exclude(depth=1)

            for page in english_pages:
                # Check if the page has a translation in the target locale
                translated_page = page.get_translation_or_none(locale)

                if not translated_page:
                    # Create the translation
                    self.stdout.write(
                        f"Translating page '{page.title}' into {locale.language_code}"
                    )

                    # Get or create translation source
                    source, created = TranslationSource.get_or_create_from_instance(page)

                    # Create or get the translation
                    translation, _ = Translation.objects.get_or_create(
                        source=source,
                        target_locale=locale,
                    )

                    # Save the target to create the translated page
                    translation.save_target()

                    self.stdout.write(
                        f"Created translation for page '{page.title}' into {locale.language_code}"
                    )
                else:
                    self.stdout.write(
                        f"Page '{page.title}' already translated into {locale.language_code}"
                    )
