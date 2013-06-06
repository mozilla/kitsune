import mock
from nose.tools import eq_

import kitsune.dashboards.personal
from kitsune.dashboards.models import GroupDashboard
from kitsune.dashboards.personal import Dashboard, personal_dashboards
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import user, group


class ATestDashboard(Dashboard):
    slug = 'sea'


class DashboardsTests(TestCase):
    """Tests for the personal_dashboards() function"""

    @mock.patch.object(kitsune.dashboards.personal,
                       'GROUP_DASHBOARDS',
                       {ATestDashboard.slug: ATestDashboard})
    def test_personal_dashboards(self):
        """Verify no obvious explosions"""
        g = group(name='winners', save=True)
        g2 = group(name='losers', save=True)
        u = user(save=True)
        u.groups.add(g)
        u.groups.add(g2)

        GroupDashboard.objects.create(group=g, dashboard='sea', parameters='1')
        GroupDashboard.objects.create(group=g2, dashboard='sea',
                                      parameters='3')

        class MockRequest(object):
            user = u

        request = MockRequest()
        dashes = personal_dashboards(request)
        # Sort order of the two ATestDashboards is by group name.
        eq_(2, len(dashes))
        eq_('3', dashes[0].parameters)
        eq_(g, dashes[1].group)
