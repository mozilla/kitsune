from datetime import datetime, timedelta

from django.core.exceptions import ValidationError

from nose.tools import eq_

from kitsune.products.tests import product, version
from kitsune.sumo.tests import TestCase


class VersionModelTests(TestCase):

    def testDefaultUnique(self):
        """Only one version can be default at a time per product."""
        prod = product(save=True)
        v1 = version(product=prod, save=True)
        v2 = version(product=prod, save=True)

        v1.default = True
        v1.save()
        v2.default = True
        try:
            v2.save()
            assert False, "No exception was thrown."
        except ValidationError:
            assert True
