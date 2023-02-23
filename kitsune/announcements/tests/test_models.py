from datetime import datetime, timedelta

from kitsune.announcements.models import Announcement
from kitsune.announcements.tests import AnnouncementFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.tests import LocaleFactory


class AnnouncementModelTests(TestCase):
    def setUp(self):
        super(AnnouncementModelTests, self).setUp()
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
        """If no groups are passed, nothing is returned."""
        # Site-wide announcement
        AnnouncementFactory()
        # Announcement in a group.
        a = AnnouncementFactory()
        a.groups.add(self.group)

        group_ann = Announcement.get_for_groups([self.group.id])
        self.assertEqual(1, len(group_ann))
        self.assertEqual(a, group_ann[0])

    def test_get_for_locale_name(self):
        """Announcements for a specific locale are shown."""
        # Site-wide announcement
        AnnouncementFactory()
        # Announcement in a locale
        a = AnnouncementFactory(locale=self.locale)

        locale_ann = Announcement.get_for_locale_name(self.locale.locale)
        self.assertEqual(1, locale_ann.count())
        self.assertEqual(a, locale_ann[0])
