from datetime import datetime, timedelta

from kitsune.announcements.models import Announcement
from kitsune.announcements.tests import AnnouncementFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.tests import LocaleFactory


class AnnouncementModelTests(TestCase):
    def setUp(self):
        super().setUp()
        self.creator = UserFactory()
        self.group = GroupFactory()
        self.locale = LocaleFactory(locale="es")
        self.creator.groups.add(self.group)

    def test_active(self):
        """Active announcement shows."""
        AnnouncementFactory(
            show_after=datetime.now() - timedelta(days=2),
            show_until=datetime.now() + timedelta(days=2),
        )
        self.assertEqual(1, Announcement.get_site_wide().count())

    def test_always_visible(self):
        """Always visible announcements are shown."""
        # This one doesn't show
        AnnouncementFactory(show_after=datetime.now() + timedelta(days=2))
        AnnouncementFactory(
            show_after=datetime.now() - timedelta(days=2), content="stardate 43125"
        )

        site_wide = Announcement.get_site_wide()
        self.assertEqual(1, site_wide.count())
        self.assertEqual("stardate 43125", site_wide[0].content)

    def test_group_excluded(self):
        """Announcements in a group are not shown."""
        announcement = AnnouncementFactory()
        announcement.groups.add(self.group)
        self.assertEqual(0, Announcement.get_site_wide().count())

    def test_get_for_groups(self):
        """Test that get_for_groups returns both site-wide and group-specific announcements."""
        # Site-wide announcement
        site_wide_ann = AnnouncementFactory()
        # Announcement in a group
        group_ann = AnnouncementFactory()
        group_ann.groups.add(self.group)

        # Should return both announcements
        announcements = Announcement.get_for_groups([self.group.id])
        self.assertEqual(2, announcements.count())
        self.assertIn(site_wide_ann, announcements)
        self.assertIn(group_ann, announcements)

        # For a different group, should only return site-wide announcement
        other_group = GroupFactory()
        announcements = Announcement.get_for_groups([other_group.id])
        self.assertEqual(1, announcements.count())
        self.assertIn(site_wide_ann, announcements)
        self.assertNotIn(group_ann, announcements)

        # For no groups, should only return site-wide announcement
        announcements = Announcement.get_for_groups([])
        self.assertEqual(1, announcements.count())
        self.assertIn(site_wide_ann, announcements)
        self.assertNotIn(group_ann, announcements)

    def test_get_for_locale_name(self):
        """Announcements for a specific locale are shown."""
        # Site-wide announcement
        AnnouncementFactory()
        # Announcement in a locale
        a = AnnouncementFactory(locale=self.locale)

        locale_ann = Announcement.get_for_locale_name(self.locale.locale)
        self.assertEqual(1, locale_ann.count())
        self.assertEqual(a, locale_ann[0])
