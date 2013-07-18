from django.db.models import (CharField, DateField, ForeignKey,
                              PositiveIntegerField)

from kitsune.sumo.models import ModelBase


VISITORS_METRIC_CODE = 'general keymetrics:visitors'
L10N_METRIC_CODE = 'general l10n:coverage'
AOA_CONTRIBUTORS_METRIC_CODE = 'general aoa:contributors'
SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE = 'general supportforum:contributors'
KB_ENUS_CONTRIBUTORS_METRIC_CODE = 'general kb:en-US:contributors'
KB_L10N_CONTRIBUTORS_METRIC_CODE = 'general kb:l10n:contributors'
SEARCH_SEARCHES_METRIC_CODE = 'search clickthroughs:elastic:searches'
SEARCH_CLICKS_METRIC_CODE = 'search clickthroughs:elastic:clicks'
EXIT_SURVEY_YES_CODE = 'exit-survey:yes'
EXIT_SURVEY_NO_CODE = 'exit-survey:no'
EXIT_SURVEY_DONT_KNOW_CODE = 'exit-survey:dont-know'


class MetricKind(ModelBase):
    """A programmer-readable identifier of a metric, like 'clicks: search'"""
    code = CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.code


class Metric(ModelBase):
    """A single numeric measurement aggregated over a span of time.

    For example, the number of hits to a page during a specific week.

    """
    # If we need to (and I would prefer to avoid this, because it wrecks the
    # consistent semantics of rows--some will be aggregations and others will
    # not), we can lift the unique constraint on kind/start/end for things that
    # are collected in realtime and can't be immediately bucketed. However, in
    # such cases it would probably be nicer to our future selves to put them in
    # a separate store (table or whatever) until bucketing.

    # In the design of this table, we trade off constraints for generality.
    # There's no way to have the DB prove, for example, that both halves of a
    # clickthrough rate ratio will always exist, but the app can make sure it's
    # true upon inserting them.

    kind = ForeignKey(MetricKind)
    start = DateField()

    # Not useful yet. Present metrics have spans of known length.
    end = DateField()

    # Ints should be good enough for all the currently wish-listed metrics.
    # Percents can be (even better) represented by 2 separate metrics: one for
    # numerator, one for denominator.
    value = PositiveIntegerField()

    class Meta(object):
        unique_together = [('kind', 'start', 'end')]

    def __unicode__(self):
        return '%s (%s thru %s): %s' % (
            self.kind, self.start, self.end, self.value)
