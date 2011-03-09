from datetime import datetime, timedelta

from nose.tools import eq_

from django.contrib.auth.models import User, Group

from announcements.models import Announcement
from sumo.tests import TestCase


class AnnouncementModelTests(TestCase):
    fixtures = ['users.json']
    content = "*crackles* Captain's log, stardate 43124.5 We are doomed."

    def setUp(self):
        super(AnnouncementModelTests, self).setUp()
        self.creator = User.objects.all()[0]

    def test_active(self):
        """Active announcement shows."""
        Announcement.objects.create(
            creator=self.creator,
            show_after=datetime.now() - timedelta(days=2),
            show_until=datetime.now() + timedelta(days=2),
            content=self.content)

        eq_(1, Announcement.get_site_wide().count())

    def test_always_visible(self):
        """Always visible announcements are shown."""
        Announcement.objects.create(
            creator=self.creator,
            show_after=datetime.now() + timedelta(days=2),  # Doesn't show
            content=self.content)
        Announcement.objects.create(
            creator=self.creator,
            show_after=datetime.now() - timedelta(days=2),
            content='stardate 43125')

        site_wide = Announcement.get_site_wide()
        eq_(1, site_wide.count())
        eq_('stardate 43125', site_wide[0].content)

    def test_group_excluded(self):
        """Announcements in a group are not shown."""
        Announcement.objects.create(
            creator=self.creator, content=self.content,
            group=Group.objects.all()[0])

        eq_(0, Announcement.get_site_wide().count())

    def test_get_for_group(self):
        """Announcements for a specific group are shown."""
        # Site-wide announcement
        Announcement.objects.create(creator=self.creator, content=self.content)
        # Announcement in our group.
        group = Group.objects.all()[0]
        a = Announcement.objects.create(
            show_after=datetime.now() - timedelta(days=2),
            creator=self.creator, content=self.content,
            group=group)

        group_ann = Announcement.get_for_group(group.name)
        eq_(1, group_ann.count())
        eq_(a, group_ann[0])
