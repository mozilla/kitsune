from django.db.models import (CharField, DateField, ForeignKey,
                              PositiveIntegerField)

from sumo.models import ModelBase


class MetricKind(ModelBase):
    """A programmer-readable identifier of a metric, like 'clicks: search'"""
    code = CharField(max_length=255, db_index=True)


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

    kind = ForeignKey(MetricKind)
    start = DateField()
    end = DateField()
    
    # Ints should be good enough for all the currently wish-listed metrics.
    # Percents can be (even better) represented by 2 separate metrics: one for
    # numerator, one for denominator.
    value = PositiveIntegerField()

    class Meta(object):
        unique_together = [('kind', 'start', 'end')]
