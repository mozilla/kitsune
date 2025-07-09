from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.termcolors import make_style
from django.db.models import Count, F

from kitsune.wiki.models import Document


SUPPORTED_LOCALES = [loc for loc in settings.SUMO_LANGUAGES if loc not in ("en-US", "xx")]

CORE_LOCALES = ["de", "es", "fr", "it", "zh-CN"]

MOST_REQUESTED_LOCALES = CORE_LOCALES + ["ja", "ru", "pt-BR", "pl", "nl"]


def get_number_fully_localized_in(locales, all_up_to_date=False):
    """
    Get the number of localizable docs that have been localized in all of the given
    locales, and optionally, only those where all of their localizations are up-to-date.
    """
    qs = Document.objects.filter(
        is_archived=False,
        locale__in=locales,
        parent__isnull=False,
        current_revision__isnull=False,
        parent__locale=settings.WIKI_DEFAULT_LANGUAGE,
        parent__is_archived=False,
        parent__is_localizable=True,
        parent__current_revision__isnull=False,
        parent__latest_localizable_revision__isnull=False,
    )

    if all_up_to_date:
        qs = qs.filter(
            current_revision__based_on_id__gte=F("parent__latest_localizable_revision_id")
        )

    return qs.values("parent").annotate(count=Count("pk")).filter(count=len(locales)).count()


class Command(BaseCommand):
    help = "Collects and reports a set of localization metrics."

    def handle(self, **options):
        self.stdout.write("-" * 85)
        self.stdout.write(f"L10N Metrics Report ({datetime.now()})")
        self.stdout.write("-" * 85)
        self.stdout.write(f"Core locales: {', '.join(loc for loc in CORE_LOCALES)}")
        self.stdout.write(
            f"Most-requested locales: {', '.join(loc for loc in MOST_REQUESTED_LOCALES)}"
        )
        self.stdout.write("-" * 85)

        bold_style = make_style(opts=("bold",))

        number_of_localizable_docs = Document.objects.filter(
            parent=None,
            locale=settings.WIKI_DEFAULT_LANGUAGE,
            is_archived=False,
            is_localizable=True,
            current_revision__isnull=False,
            latest_localizable_revision__isnull=False,
        ).count()

        self.stdout.write(
            f"Total localizable KB articles: {bold_style(number_of_localizable_docs)}"
        )
        self.stdout.write("-" * 85)

        if number_of_localizable_docs == 0:
            return

        def show_results_for(locales, name):
            number_fully_localized = get_number_fully_localized_in(locales)

            if number_fully_localized:
                percentage = (number_fully_localized / number_of_localizable_docs) * 100
                percentage_up_to_date = (
                    get_number_fully_localized_in(locales, all_up_to_date=True)
                    / number_fully_localized
                ) * 100
            else:
                percentage = 0
                percentage_up_to_date = 0

            percentage = bold_style(f"{percentage:>5.1f}%")
            percentage_up_to_date = bold_style(f"{percentage_up_to_date:>5.1f}%")

            self.stdout.write(
                f"Available in {name:>30}: {percentage}"
                f"  ({percentage_up_to_date} are up-to-date"
                f"{' in all' if len(locales) > 1 else ''})"
            )

        show_results_for(CORE_LOCALES, "all core locales")
        show_results_for(MOST_REQUESTED_LOCALES, "all most-requested locales")
        for locale in sorted(SUPPORTED_LOCALES):
            show_results_for([locale], f"{settings.LOCALES[locale].english} ({locale})")
