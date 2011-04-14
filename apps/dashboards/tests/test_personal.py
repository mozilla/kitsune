from django.contrib.auth.models import Group

import mock
from nose.tools import eq_

from dashboards.models import GroupDashboard
import dashboards.personal
from dashboards.personal import Dashboard, personal_dashboards, ReviewDashboard
from sumo.tests import TestCase
from users.tests import user


class DictDashboard(Dashboard):
    """Dashboard that uses a dict for its params"""
    slug = 'sea'

    def digested_params(self, params):
        return {'stuff': params}


class FlatDashboard(Dashboard):
    """Dashboard that represents its params just as they're passed in"""
    slug = 'earth'


class AnotherDashboard(Dashboard):
    """Dashboard that represents its params just as they're passed in"""
    slug = 'other'


class BaseClassTests(TestCase):
    """Tests for the Dashboards base class"""

    def test_compare_by_value(self):
        """Make sure Dashboard instances compare according to instance vars."""
        eq_(FlatDashboard(3, 'fred'), FlatDashboard(3, 'fred'))

    def test_differ_by_class(self):
        """Dashboard subclass instances must compare different when of
        different slugs."""
        assert FlatDashboard(3, 'fred') != AnotherDashboard(3, 'fred')

    def test_unique_in_set(self):
        """Dashboard subclasses instances must hash differently when having
        different slugs, the same when having the same."""
        eq_(1, len(set([FlatDashboard(3, 'fred'),
                        FlatDashboard(3, 'fred')])))
        eq_(2, len(set([FlatDashboard(3, 'fred'),
                        AnotherDashboard(3, 'fred')])))

    def test_dict_unique_in_set(self):
        """Ensure hashing works when using dicts for Dashboard._params."""
        eq_(1, len(set([DictDashboard(3, 'fred'), DictDashboard(3, 'fred')])))
        eq_(2, len(set([DictDashboard(3, 'fred'), DictDashboard(3, 'jorg')])))


class DashboardsTests(TestCase):
    """Tests for the personal_dashboards() function"""

    @mock.patch.object(dashboards.personal,
                       'DYNAMIC_DASHBOARDS',
                       {DictDashboard.slug: DictDashboard})
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
        # Sort order of the two DictDashboards is indeterminite at the moment.
        assert dashes in [[ReviewDashboard(request),
                           DictDashboard(request, '1'),
                           DictDashboard(request, '2')],
                          [ReviewDashboard(request),
                           DictDashboard(request, '2'),
                           DictDashboard(request, '1')]]
