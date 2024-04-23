import logging

from django.db import IntegrityError, models, transaction
from django.db.models import Subquery
from django.utils.translation import gettext_lazy as _lazy

from kitsune.dashboards import PERIODS
from kitsune.products.models import Product
from kitsune.sumo import googleanalytics
from kitsune.sumo.models import LocaleField, ModelBase
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

            # Then we can create the fresh results for this period.
            if verbose:
                log.info(f"Creating fresh instances of {cls.__name__} with period = {period}...")

            for (locale, slug), visits in googleanalytics.pageviews_by_document(
                period, verbose=verbose
            ):
                try:
                    with transaction.atomic():
                        cls.objects.create(
                            document_id=Subquery(
                                Document.objects.filter(locale=locale, slug=slug).values("id")
                            ),
                            period=period,
                            visits=visits,
                        )
                except IntegrityError:
                    # We've already rolled back the bad insertion, which was due to the
                    # fact that the document no longer exists, so let's move on.
                    pass


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
