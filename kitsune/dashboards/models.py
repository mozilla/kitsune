import logging
from datetime import date, timedelta

from django.conf import settings
from django.db import connection, close_old_connections
from django.db import models
from django.utils.translation import ugettext_lazy as _lazy

from kitsune.dashboards import (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS,
                                ALL_TIME, PERIODS)
from kitsune.products.models import Product
from kitsune.sumo.models import ModelBase, LocaleField
from kitsune.sumo import googleanalytics
from kitsune.wiki.models import Document


log = logging.getLogger('k.dashboards')


def period_dates(period):
    """Return when each period begins and ends."""
    end = date.today() - timedelta(days=1)  # yesterday

    if period == LAST_7_DAYS:
        start = end - timedelta(days=7)
    elif period == LAST_30_DAYS:
        start = end - timedelta(days=30)
    elif period == LAST_90_DAYS:
        start = end - timedelta(days=90)
    elif ALL_TIME:
        start = settings.GA_START_DATE

    return start, end


class WikiDocumentVisits(ModelBase):
    """Web stats for Knowledge Base Documents"""

    document = models.ForeignKey(Document, related_name='visits')
    visits = models.IntegerField(db_index=True)
    period = models.IntegerField(choices=PERIODS)  # indexed by unique_together

    class Meta(object):
        unique_together = ('period', 'document')

    @classmethod
    def reload_period_from_analytics(cls, period, verbose=False):
        """Replace the stats for the given period from Google Analytics."""
        counts = googleanalytics.pageviews_by_document(
            *period_dates(period), verbose=verbose)
        if counts:
            # Close any existing connections because our load balancer times
            # them out at 5 minutes and the GA calls take forever.
            close_old_connections()

            # Delete and remake the rows:
            # Horribly inefficient until
            # http://code.djangoproject.com/ticket/9519 is fixed.
            # cls.objects.filter(period=period).delete()

            # Instead, we use raw SQL!
            cursor = connection.cursor()
            cursor.execute(
                'DELETE FROM `dashboards_wikidocumentvisits`'
                '    WHERE `period` = %s',
                [period])

            # Now we create them again with fresh data.
            for doc_id, visits in counts.items():
                cls.objects.create(document=Document(pk=doc_id), visits=visits,
                                   period=period)
        else:
            # Don't erase interesting data if there's nothing to replace it:
            log.warning('Google Analytics returned no interesting data,'
                        ' so I kept what I had.')


L10N_TOP20_CODE = 'percent_localized_top20'
L10N_TOP100_CODE = 'percent_localized_top100'
L10N_ALL_CODE = 'percent_localized_all'
L10N_ACTIVE_CONTRIBUTORS_CODE = 'active_contributors'
METRIC_CODE_CHOICES = (
    (L10N_TOP20_CODE, _lazy('Percent Localized: Top 20')),
    (L10N_TOP100_CODE, _lazy('Percent Localized: Top 100')),
    (L10N_ALL_CODE, _lazy('Percent Localized: All')),
    (L10N_ACTIVE_CONTRIBUTORS_CODE,
     _lazy('Monthly Active Contributors')),
)


class WikiMetric(ModelBase):
    """A single numeric measurement for a locale, product and date.

    For example, the percentage of all FxOS articles localized to Spanish."""
    code = models.CharField(
        db_index=True, max_length=255, choices=METRIC_CODE_CHOICES)
    locale = LocaleField(db_index=True, null=True, blank=True)
    product = models.ForeignKey(Product, null=True, blank=True)
    date = models.DateField()
    value = models.FloatField()

    class Meta(object):
        unique_together = ('code', 'product', 'locale', 'date')
        ordering = ['-date']

    def __unicode__(self):
        return '[{date}][{locale}][{product}] {code}: {value}'.format(
            date=self.date, code=self.code, locale=self.locale,
            value=self.value, product=self.product)
