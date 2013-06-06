from datetime import date

from kitsune.kpi.models import MetricKind, Metric
from kitsune.sumo.tests import with_save


@with_save
def metric_kind(**kwargs):
    return MetricKind(code=kwargs.get('code', 'something'))


@with_save
def metric(**kwargs):
    defaults = {'start': date(1980, 02, 16),
                'end': date(1980, 02, 23),
                'value': 33}
    if 'kind' not in kwargs:
        defaults['kind'] = metric_kind(save=True)
    defaults.update(kwargs)
    return Metric(**defaults)
