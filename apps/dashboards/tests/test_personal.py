from django.contrib.auth.models import Group

import mock
from nose.tools import eq_

from dashboards.models import GroupDashboard
import dashboards.personal
from dashboards.personal import Dashboard, personal_dashboards, ReviewDashboard
from sumo.tests import TestCase
from users.tests import user


class MockDashboard(Dashboard):
    slug = 'sea'

    def __init__(self, request, params=''):
        super(MockDashboard, self).__init__(request, params)
        self._params = {'stuff': params}


class BaseClassTests(TestCase):
    """Tests for the Dashboards base class"""

    def test_compare_by_value(self):
        """Make sure Dashboard instances compare according to instance vars."""
        eq_(Dashboard(3, 'fred'), Dashboard(3, 'fred'))

    def test_differ_by_class(self):
        """Dashboard subclass instances must compare different when of
        different classes."""
        assert Dashboard(3, 'fred') != MockDashboard(3, 'fred')

    def test_unique_in_set(self):
        """Dashboard subclass instances must compare different when of
        different classes."""
        eq_(1, len(set([Dashboard(3, 'fred'), Dashboard(3, 'fred')])))
        eq_(2, len(set([Dashboard(3, 'fred'), MockDashboard(3, 'fred')])))


class DashboardsTests(TestCase):
    """Tests for the personal_dashboards() function"""

    @mock.patch.object(dashboards.personal,
                       'DYNAMIC_DASHBOARDS',
                       {MockDashboard.slug: MockDashboard})
    @mock.patch.object(dashboards.personal,
                       'STATIC_DASHBOARDS',
                       [ReviewDashboard])
    def test_personal_dashboards(self):
        """Just run through it to make sure there aren't obvious explosions."""
        g = Group.objects.create(name='losers')
        u = user(save=True)
        u.groups.add(g)

        GroupDashboard.objects.create(group=g, dashboard='sea', parameters='1')
        GroupDashboard.objects.create(group=g, dashboard='sea', parameters='2')
        GroupDashboard.objects.create(group=g, dashboard='sea', parameters='1')

        class MockRequest(object):
            user = u

        request = MockRequest()
        dashes = personal_dashboards(request)
        # Sort order of the two MockDashboards is indeterminite at the moment.
        assert dashes in [[ReviewDashboard(request),
                           MockDashboard(request, '1'),
                           MockDashboard(request, '2')],
                          [ReviewDashboard(request),
                           MockDashboard(request, '1'),
                           MockDashboard(request, '2')]]
