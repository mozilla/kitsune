from datetime import date

from kitsune.dashboards.models import WikiMetric
from kitsune.products.tests import product
from kitsune.sumo.tests import with_save


@with_save
def wiki_metric(**kwargs):
    """A model maker for WikiMetric."""
    defaults = {'code': 'test_code',
                'locale': 'es',
                'date': date.today(),
                'value': 42.0}

    if 'product' not in kwargs:
        defaults['product'] = product(save=True)

    defaults.update(kwargs)

    return WikiMetric(**defaults)
