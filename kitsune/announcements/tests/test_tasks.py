from unittest import mock

from django.contrib.sites.models import Site
from django.core import mail
from nose.tools import eq_

from kitsune.announcements.tasks import send_group_email
from kitsune.announcements.tests import AnnouncementFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory
from kitsune.users.tests import UserFactory


class AnnouncementSaveTests(TestCase):
    """Test creating group announcements."""

    def _setup_announcement(self, visible_dates=True):
        g = GroupFactory()
        u1 = UserFactory(groups=[g])
        u2 = UserFactory(groups=[g])
        self.user = u2

        return AnnouncementFactory(creator=u1, group=g, visible_dates=visible_dates)

    @mock.patch.object(Site.objects, "get_current")
    def test_create_announcement(self, get_current):
        """An announcement is created and email is sent to group members."""
        get_current.return_value.domain = "testserver"

        a = self._setup_announcement()

        # Signal fired, emails sent.
        eq_(2, len(mail.outbox))
        assert a.content in mail.outbox[0].body
        assert a.content in mail.outbox[1].body

        # No new emails sent when modifying.
        a.creator = self.user
        a.save()
        eq_(2, len(mail.outbox))

    @mock.patch.object(Site.objects, "get_current")
    def test_create_invisible_announcement(self, get_current):
        """No emails sent if announcement is not visible."""
        get_current.return_value.domain = "testserver"

        self._setup_announcement(visible_dates=False)
        eq_(0, len(mail.outbox))

    @mock.patch.object(Site.objects, "get_current")
    def test_send_nonexistent(self, get_current):
        """Send a non-existent announcement by email shouldn't break."""
        get_current.return_value.domain = "testserver"

        send_group_email(1)
        eq_(0, len(mail.outbox))
