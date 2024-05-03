import logging

from django.db import IntegrityError, models, transaction
from django.db.models import Q, Subquery
from django.utils.translation import gettext_lazy as _lazy

from kitsune.dashboards import PERIODS
from kitsune.products.models import Product
from kitsune.sumo import googleanalytics
from kitsune.sumo.models import LocaleField, ModelBase
from kitsune.sumo.utils import chunked
from kitsune.wiki.models import Document

log = logging.getLogger("k.dashboards")


class WikiDocumentVisits(ModelBase):
    """Web stats for Knowledge Base Documents"""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="visits")
    visits = models.IntegerField(db_index=True)
    period = models.IntegerField(choices=PERIODS)  # indexed by unique_together

    class Meta(object):
        unique_together = ("period", "document")

    @classmethod
    def reload_period_from_analytics(cls, period, verbose=False):
        """Replace the stats for the given period from Google Analytics."""
        with transaction.atomic():
            # First, let's clear out the previous results for this period.
            if verbose:
                log.info(
                    f"Deleting all stale instances of {cls.__name__} with period = {period}..."
                )

            cls.objects.filter(period=period).delete()

            # Next, let's gather some data we need. We're sacrificing memory
            # here in order to reduce the number of database queries later on.
            if verbose:
                log.info("Gathering pageviews per article from GA4 data API...")

            instance_by_locale_and_slug = {}
            for (locale, slug), visits in googleanalytics.pageviews_by_document(
                period, verbose=verbose
            ):
                instance_by_locale_and_slug[(locale, slug)] = cls(
                    document_id=Subquery(
                        Document.objects.filter(locale=locale, slug=slug).values("id")
                    ),
                    period=period,
                    visits=visits,
                )

            # Then we can create the fresh results for this period.
            if verbose:
                log.info(
                    f"Creating {len(instance_by_locale_and_slug)} fresh instances of "
                    f"{cls.__name__} with period = {period}..."
                )

            def create_batch(batch_of_locale_and_slug_queries):
                """
                Create a batch of instances in one shot, but only include instances that
                refer to an existing Document, so we avoid triggering an integrity error.
                A call to this function makes only two databases queries no matter how
                many instances we need to validate and create.
                """
                cls.objects.bulk_create(
                    [
                        instance_by_locale_and_slug[locale_and_slug]
                        for locale_and_slug in Document.objects.filter(
                            batch_of_locale_and_slug_queries
                        ).values_list("locale", "slug")
                    ]
                )

            # Let's create the fresh instances in batches, so we avoid exposing ourselves to
            # the possibility of transgressing some query size limit.
            batch_size = 1000
            for batch_of_pairs in chunked(list(instance_by_locale_and_slug), batch_size):
                locale_and_slug_queries = Q()
                for locale, slug in batch_of_pairs:
                    locale_and_slug_queries |= Q(locale=locale, slug=slug)

                if verbose:
                    log.info(f"Creating a batch of {len(batch_of_pairs)} instances...")

                try:
                    with transaction.atomic():
                        create_batch(locale_and_slug_queries)
                except IntegrityError:
                    # There is a very slim chance that one or more Documents have been deleted in
                    # the moment of time between the formation of the list of valid instances and
                    # actually creating them, so let's give it one more try, assuming there's an
                    # even slimmer chance that lightning will strike twice. If this one fails,
                    # we'll roll-back everything and give up on the entire effort.
                    create_batch(locale_and_slug_queries)

            if verbose:
                log.info("Done.")


L10N_TOP20_CODE = "percent_localized_top20"
L10N_TOP100_CODE = "percent_localized_top100"
L10N_ALL_CODE = "percent_localized_all"
L10N_ACTIVE_CONTRIBUTORS_CODE = "active_contributors"
METRIC_CODE_CHOICES = (
    (L10N_TOP20_CODE, _lazy("Percent Localized: Top 20")),
    (L10N_TOP100_CODE, _lazy("Percent Localized: Top 100")),
    (L10N_ALL_CODE, _lazy("Percent Localized: All")),
    (L10N_ACTIVE_CONTRIBUTORS_CODE, _lazy("Monthly Active Contributors")),
)


class WikiMetric(ModelBase):
    """A single numeric measurement for a locale, product and date.

    For example, the percentage of all FxOS articles localized to Spanish."""

    code = models.CharField(db_index=True, max_length=255, choices=METRIC_CODE_CHOICES)
    locale = LocaleField(db_index=True, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    value = models.FloatField()

    class Meta(object):
        unique_together = ("code", "product", "locale", "date")
        ordering = ["-date"]

    def __str__(self):
        return "[{date}][{locale}][{product}] {code}: {value}".format(
            date=self.date,
            code=self.code,
            locale=self.locale,
            value=self.value,
            product=self.product,
        )
