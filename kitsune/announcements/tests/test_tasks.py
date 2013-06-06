from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_

from kitsune.announcements.tasks import send_group_email
from kitsune.announcements.tests import announcement
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import user, group, profile


class AnnouncementSaveTests(TestCase):
    """Test creating group announcements."""

    def _setup_announcement(self, visible_dates=True):
        g = group(save=True)
        u1 = user(save=True)
        u2 = user(save=True)
        u1.groups.add(g)
        u2.groups.add(g)
        # Create profiles for these users
        profile(user=u1)
        profile(user=u2)
        self.user = u2

        return announcement(creator=u1, group=g, save=True,
                            visible_dates=visible_dates)

    @mock.patch.object(Site.objects, 'get_current')
    def test_create_announcement(self, get_current):
        """An announcement is created and email is sent to group members."""
        get_current.return_value.domain = 'testserver'

        a = self._setup_announcement()

        # Signal fired, emails sent.
        eq_(2, len(mail.outbox))
        assert 'stardate' in mail.outbox[0].body
        assert 'stardate' in mail.outbox[1].body

        # No new emails sent when modifying.
        a.creator = self.user
        a.save()
        eq_(2, len(mail.outbox))

    @mock.patch.object(Site.objects, 'get_current')
    def test_create_invisible_announcement(self, get_current):
        """No emails sent if announcement is not visible."""
        get_current.return_value.domain = 'testserver'

        self._setup_announcement(visible_dates=False)
        eq_(0, len(mail.outbox))

    @mock.patch.object(Site.objects, 'get_current')
    def test_send_nonexistent(self, get_current):
        """Send a non-existent announcement by email shouldn't break."""
        get_current.return_value.domain = 'testserver'

        send_group_email(1)
        eq_(0, len(mail.outbox))
