from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.dashboards.models import L10N_ALL_CODE
from kitsune.dashboards.models import L10N_TOP100_CODE
from kitsune.dashboards.models import L10N_TOP20_CODE
from kitsune.dashboards.models import WikiMetric
from kitsune.dashboards.readouts import l10n_overview_rows
from kitsune.products.models import Product


class Command(BaseCommand):
    help = "Calculate and store the l10n metrics for each locale/product."

    def handle(self, **options):
        """
        The metrics are:
        * Percent localized of top 20 articles
        * Percent localized of all articles
        """
        today = date.today()

        # Loop through all locales.
        for locale in settings.SUMO_LANGUAGES:

            # Skip en-US, it is always 100% localized.
            if locale == settings.WIKI_DEFAULT_LANGUAGE:
                continue

            # Loop through all enabled products, including None (really All).
            for product in [None] + list(Product.objects.filter(visible=True)):

                # (Ab)use the l10n_overview_rows helper from the readouts.
                rows = l10n_overview_rows(locale=locale, product=product)

                # % of top 20 articles
                top20 = rows['top-20']

                try:
                    percent = 100.0 * float(top20['numerator']) / top20['denominator']
                except ZeroDivisionError:
                    percent = 0.0

                WikiMetric.objects.create(
                    code=L10N_TOP20_CODE,
                    locale=locale,
                    product=product,
                    date=today,
                    value=percent)

                # % of top 100 articles
                top100 = rows['top-100']

                try:
                    percent = 100.0 * float(top100['numerator']) / top100['denominator']
                except ZeroDivisionError:
                    percent = 0.0

                WikiMetric.objects.create(
                    code=L10N_TOP100_CODE,
                    locale=locale,
                    product=product,
                    date=today,
                    value=percent)

                # % of all articles
                all_ = rows['all']
                try:
                    percent = 100 * float(all_['numerator']) / all_['denominator']
                except ZeroDivisionError:
                    percent = 0.0

                WikiMetric.objects.create(
                    code=L10N_ALL_CODE,
                    locale=locale,
                    product=product,
                    date=today,
                    value=percent)
