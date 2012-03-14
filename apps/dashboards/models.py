import json
import logging

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models

from tower import ugettext_lazy as _lazy

from dashboards import (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS, ALL_TIME,
                        PERIODS)
from dashboards.personal import GROUP_DASHBOARDS
from sumo.models import ModelBase
from sumo.webtrends import Webtrends, StatsException
from wiki.models import Document


log = logging.getLogger('k.dashboards')


def period_dates():
    """Return when each period begins and ends, relative to now.

    Return values are in the format WebTrends likes: "2010m01d30" or
    "current_day-7".

    """
    # WebTrends' server apparently runs in UTC, FWIW.
    yesterday = 'current_day-1'  # Start at yesterday so we get a full week of
                                 # data.
    return {LAST_7_DAYS: ('current_day-7', yesterday),
            LAST_30_DAYS: ('current_day-30', yesterday),
            LAST_90_DAYS: ('current_day-90', yesterday),
            ALL_TIME: (settings.WEBTRENDS_EPOCH.strftime('%Ym%md%d'),
                       yesterday)}


class WikiDocumentVisits(ModelBase):
    """Web stats for Knowledge Base Documents"""

    document = models.ForeignKey(Document)
    visits = models.IntegerField(db_index=True)
    period = models.IntegerField(choices=PERIODS)  # indexed by unique_together

    class Meta(object):
        unique_together = ('period', 'document')

    @classmethod
    def reload_period_from_json(cls, period, json_data):
        """Replace the stats for the given period with the given JSON."""
        counts = cls._visit_counts(json_data)
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
            log.warning('WebTrends returned no interesting data, so I kept '
                        'what I had.')

    @classmethod
    def _visit_counts(cls, json_data):
        """Given WebTrends JSON data, return a dict of doc IDs and visits:

            {document ID: number of visits, ...}

        If there is no interesting data in the given JSON, return {}.

        """
        # We're very defensive here, as WebTrends has been known to return
        # invalid garbage of various sorts.
        try:
            data = json.loads(json_data)['data']
        except (ValueError, KeyError, TypeError):
            raise StatsException('Error extracting data from WebTrends JSON')

        try:
            pages = (data[data.keys()[0]]['SubRows'] if data.keys()
                     else {}).iteritems()
        except (AttributeError, IndexError, KeyError, TypeError):
            raise StatsException('Error extracting pages from WebTrends data')

        counts = {}
        for url, page_info in pages:
            doc = Document.from_url(
                url,
                required_locale=settings.LANGUAGE_CODE,
                id_only=True,
                check_host=False)
            if not doc:
                continue

            # Get visit count:
            try:
                visits = int(page_info['measures']['Visits'])
            except (ValueError, KeyError, TypeError):
                continue

            # Sometimes WebTrends repeats a URL modulo a space, .com vs .org,
            # etc. These resolve to the same document so we add them.
            if doc.pk in counts:
                counts[doc.pk] += visits
            else:
                counts[doc.pk] = visits

        return counts

    @classmethod
    def json_for(cls, period):
        """Return the JSON-formatted WebTrends stats for the given period."""
        start, end = period_dates()[period]
        return Webtrends.wiki_report(start, end)


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
