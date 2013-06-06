import logging
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models

from tower import ugettext_lazy as _lazy

from kitsune.dashboards import (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS,
                                ALL_TIME, PERIODS)
from kitsune.dashboards.personal import GROUP_DASHBOARDS
from kitsune.sumo.models import ModelBase
from kitsune.sumo import googleanalytics
from kitsune.sumo.urlresolvers import reverse
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

    document = models.ForeignKey(Document)
    visits = models.IntegerField(db_index=True)
    period = models.IntegerField(choices=PERIODS)  # indexed by unique_together

    class Meta(object):
        unique_together = ('period', 'document')

    @classmethod
    def reload_period_from_analytics(cls, period):
        """Replace the stats for the given period from Google Analytics."""
        counts = googleanalytics.pageviews_by_document(*period_dates(period))
        if counts:
            # Delete and remake the rows:
            # Horribly inefficient until
            # http://code.djangoproject.com/ticket/9519 is fixed.
            cls.objects.filter(period=period).delete()
            for doc_id, visits in counts.iteritems():
                cls.objects.create(document=Document(pk=doc_id), visits=visits,
                                   period=period)
        else:
            # Don't erase interesting data if there's nothing to replace it:
            log.warning('Google Analytics returned no interesting data,'
                        ' so I kept what I had.')


class GroupDashboard(ModelBase):
    """A mapping of a group to a dashboard available to its members.

    This can be used to map a group to more than one dashboard so we don't have
    to manage otherwise-redundant groups.

    """
    # We could have just used a permission per dashboard to do the mapping if
    # we didn't need to parametrize them.

    group = models.OneToOneField(Group, related_name='dashboard')

    # Slug of a Dashboard subclass
    dashboard = models.CharField(
        max_length=10,
        choices=sorted([(d.slug, d.__name__)
                        for d in GROUP_DASHBOARDS.values()],
                       key=lambda tup: tup[1]))

    # Might expand to a TextField if we run out of room:
    parameters = models.CharField(
        max_length=255,
        blank=True,
        help_text=_lazy(u'Parameters which will be passed to the dashboard. '
                         'The dashboard determines the meaning and format of '
                         'these.'))

    def __unicode__(self):
        return u'%s (%s)' % (self.dashboard, self.parameters)

    def get_absolute_url(self):
        return reverse('dashboards.group', args=[self.group.id])
