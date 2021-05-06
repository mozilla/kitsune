import argparse
from datetime import date, datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.dashboards.models import L10N_ACTIVE_CONTRIBUTORS_CODE, WikiMetric
from kitsune.products.models import Product
from kitsune.wiki.utils import num_active_contributors


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


class Command(BaseCommand):
    help = "Update the number of active contributors for each locale/product."

    def add_arguments(self, parser):
        parser.add_argument("day", nargs="?", type=valid_date)

    def handle(self, day=None, **options):
        """
        An active contributor is defined as a user that created or reviewed a
        revision in the previous calendar month.
        """
        if day is None:
            day = date.today()
        first_of_month = date(day.year, day.month, 1)
        if day.month == 1:
            previous_first_of_month = date(day.year - 1, 12, 1)
        else:
            previous_first_of_month = date(day.year, day.month - 1, 1)

        # Loop through all locales.
        for locale in settings.SUMO_LANGUAGES:

            # Loop through all enabled products, including None (really All).
            for product in [None] + list(Product.objects.filter(visible=True)):

                num = num_active_contributors(
                    from_date=previous_first_of_month,
                    to_date=first_of_month,
                    locale=locale,
                    product=product,
                )

                WikiMetric.objects.create(
                    code=L10N_ACTIVE_CONTRIBUTORS_CODE,
                    locale=locale,
                    product=product,
                    date=previous_first_of_month,
                    value=num,
                )
