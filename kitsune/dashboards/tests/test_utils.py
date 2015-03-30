from datetime import date

from mock import patch
from nose.tools import eq_

from kitsune.dashboards import utils
from kitsune.dashboards.utils import get_locales_by_visit
from kitsune.sumo.tests import TestCase


class DashboardUtilsTests(TestCase):

    @patch.object(utils, 'visitors_by_locale')
    def test_get_locales_by_visit(self, visitors_by_locale):
        """Verify the result of get_locales_by_visit()."""
        visitors_by_locale.return_value = {
            'de': 1674352,
            'en-US': 9381226,
            'es': 1226117,
            'fr': 1075765,
            'pt-BR': 788700,
            'ru': 950564,
        }

        results = get_locales_by_visit(date(2013, 7, 1), date(2013, 8, 1))
        eq_([('en-US', 9381226), ('de', 1674352), ('es', 1226117),
             ('fr', 1075765), ('ru', 950564), ('pt-BR', 788700)], results)
