from datetime import date

import factory

from kitsune.kpi.models import Metric
from kitsune.kpi.models import MetricKind
from kitsune.sumo.tests import FuzzyUnicode


class MetricKindFactory(factory.DjangoModelFactory):
    class Meta:
        model = MetricKind

    code = FuzzyUnicode()


class MetricFactory(factory.DjangoModelFactory):
    class Meta:
        model = Metric

    start = date(1980, 2, 16)
    end = date(1980, 2, 23)
    value = 33
    kind = factory.SubFactory(MetricKindFactory)
