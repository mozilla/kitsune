from datetime import datetime, timedelta

from kitsune.announcements.models import Announcement
from kitsune.announcements.tests import AnnouncementFactory
from kitsune.products.tests import PlatformFactory
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

    def test_for_groups(self):
        """Test that get_site_wide returns both site-wide and group-specific announcements."""
        # Site-wide announcement
        site_wide_ann = AnnouncementFactory()
        # Announcement in a group
        group_ann = AnnouncementFactory()
        group_ann.groups.add(self.group)

        # Should return both announcements
        announcements = Announcement.get_site_wide(group_ids=[self.group.id])
        self.assertEqual(2, announcements.count())
        self.assertIn(site_wide_ann, announcements)
        self.assertIn(group_ann, announcements)

        # For a different group, should only return site-wide announcement
        other_group = GroupFactory()
        announcements = Announcement.get_site_wide(group_ids=[other_group.id])
        self.assertEqual(1, announcements.count())
        self.assertIn(site_wide_ann, announcements)
        self.assertNotIn(group_ann, announcements)

        # For no groups, should only return site-wide announcement
        announcements = Announcement.get_site_wide(group_ids=[])
        self.assertEqual(1, announcements.count())
        self.assertIn(site_wide_ann, announcements)
        self.assertNotIn(group_ann, announcements)

    def test_for_locale_name(self):
        """Announcements for a specific locale are shown."""
        # Site-wide announcement
        a1 = AnnouncementFactory()
        # Announcement in a locale
        a2 = AnnouncementFactory(locale=self.locale)
        AnnouncementFactory(locale=LocaleFactory(locale="it"))

        announcements = Announcement.get_site_wide(locale_name=self.locale.locale)
        self.assertEqual(set(announcements), {a1, a2})

    def test_platform_based_filtering(self):
        """Test platform-based announcement filtering."""
        # Create platforms
        mac_platform = PlatformFactory(slug="mac", name="macOS")
        win_platform = PlatformFactory(slug="win10", name="Windows 10")
        linux_platform = PlatformFactory(slug="linux", name="Linux")

        # Site-wide announcement (no platforms)
        site_wide_ann = AnnouncementFactory()

        # macOS-targeted announcement
        mac_ann = AnnouncementFactory()
        mac_ann.platforms.add(mac_platform)

        # Windows-targeted announcement
        win_ann = AnnouncementFactory()
        win_ann.platforms.add(win_platform)

        # Multi-platform announcement
        multi_ann = AnnouncementFactory()
        multi_ann.platforms.add(mac_platform, linux_platform)

        # Test site-wide with no platform filtering
        announcements = Announcement.get_site_wide()
        self.assertEqual(4, announcements.count())
        self.assertIn(site_wide_ann, announcements)
        self.assertIn(mac_ann, announcements)
        self.assertIn(win_ann, announcements)
        self.assertIn(multi_ann, announcements)

        # Test macOS platform filtering
        mac_announcements = Announcement._visible_query(platforms=["mac"])
        self.assertEqual(3, mac_announcements.count())
        self.assertIn(site_wide_ann, mac_announcements)  # Site-wide included
        self.assertIn(mac_ann, mac_announcements)  # macOS targeted
        self.assertIn(multi_ann, mac_announcements)  # Multi-platform includes macOS
        self.assertNotIn(win_ann, mac_announcements)  # Windows targeted excluded

        # Test Windows platform filtering
        win_announcements = Announcement._visible_query(platforms=["win10"])
        self.assertEqual(2, win_announcements.count())
        self.assertIn(site_wide_ann, win_announcements)  # Site-wide included
        self.assertIn(win_ann, win_announcements)  # Windows targeted
        self.assertNotIn(mac_ann, win_announcements)  # macOS targeted excluded
        self.assertNotIn(multi_ann, win_announcements)  # Multi-platform doesn't include Windows

        # Test multiple platform filtering
        multi_platform_announcements = Announcement._visible_query(platforms=["mac", "linux"])
        self.assertEqual(3, multi_platform_announcements.count())
        self.assertIn(site_wide_ann, multi_platform_announcements)  # Site-wide included
        self.assertIn(mac_ann, multi_platform_announcements)  # macOS targeted
        self.assertIn(multi_ann, multi_platform_announcements)  # Multi-platform matches both
        self.assertNotIn(win_ann, multi_platform_announcements)  # Windows targeted excluded

    def test_combined_filtering(self):
        """Test combined filtering."""
        # Create platforms and groups
        mac_platform = PlatformFactory(slug="mac", name="macOS")
        win_platform = PlatformFactory(slug="win10", name="Windows 10")
        group1 = GroupFactory()
        group2 = GroupFactory()

        # Site-wide announcement (no platforms, no groups)
        site_wide_ann = AnnouncementFactory()

        # macOS + group1 announcement
        mac_group1_ann = AnnouncementFactory()
        mac_group1_ann.platforms.add(mac_platform)
        mac_group1_ann.groups.add(group1)

        # macOS + group1 + locale announcement
        mac_group1_locale_ann = AnnouncementFactory(locale=self.locale)
        mac_group1_locale_ann.platforms.add(mac_platform)
        mac_group1_locale_ann.groups.add(group1)

        # Windows + group2 announcement
        win_group2_ann = AnnouncementFactory()
        win_group2_ann.platforms.add(win_platform)
        win_group2_ann.groups.add(group2)

        # Windows + [group1, group2] + locale announcement
        win_groups_locale_ann = AnnouncementFactory(locale=self.locale)
        win_groups_locale_ann.platforms.add(win_platform)
        win_groups_locale_ann.groups.add(group1)
        win_groups_locale_ann.groups.add(group2)

        # macOS + no groups announcement
        mac_only_ann = AnnouncementFactory()
        mac_only_ann.platforms.add(mac_platform)

        # Test macOS user in group1
        announcements = Announcement.get_site_wide(group_ids=[group1.id], platform_slugs=["mac"])
        self.assertEqual(set(announcements), {site_wide_ann, mac_group1_ann, mac_only_ann})

        # Test macOS user in group1 or group2, and locale
        announcements = Announcement.get_site_wide(
            platform_slugs=["mac"],
            group_ids=[group1.id, group2.id],
            locale_name=self.locale.locale,
        )
        self.assertEqual(
            set(announcements),
            {site_wide_ann, mac_group1_ann, mac_group1_locale_ann, mac_only_ann},
        )

        # Test macOS user in group2
        announcements = Announcement.get_site_wide(group_ids=[group2.id], platform_slugs=["mac"])
        self.assertEqual(set(announcements), {site_wide_ann, mac_only_ann})

        # Test Windows user in group1
        announcements = Announcement.get_site_wide(group_ids=[group1.id], platform_slugs=["win10"])
        self.assertEqual(set(announcements), {site_wide_ann})

        # Test Windows user in group1 or group2, and locale
        announcements = Announcement.get_site_wide(
            platform_slugs=["win10"],
            group_ids=[group1.id, group2.id],
            locale_name=self.locale.locale,
        )
        self.assertEqual(
            set(announcements), {site_wide_ann, win_group2_ann, win_groups_locale_ann}
        )

    def test_web_platform_special_case(self):
        """Test that 'web' platform makes announcements site-wide."""
        web_platform = PlatformFactory(slug="web", name="Web")

        # Announcement with web platform
        web_ann = AnnouncementFactory()
        web_ann.platforms.add(web_platform)

        # Announcement with macOS platform
        mac_platform = PlatformFactory(slug="mac", name="macOS")
        mac_ann = AnnouncementFactory()
        mac_ann.platforms.add(mac_platform)

        # Test that web platform announcement is always included
        mac_announcements = Announcement._visible_query(platforms=["mac"])
        self.assertEqual(2, mac_announcements.count())
        self.assertIn(web_ann, mac_announcements)  # Web platform always included
        self.assertIn(mac_ann, mac_announcements)  # macOS platform included

        win_announcements = Announcement._visible_query(platforms=["win10"])
        self.assertEqual(2, win_announcements.count())
        self.assertIn(web_ann, win_announcements)  # Web platform always included
        self.assertIn(mac_ann, win_announcements)  # macOS platform included (site-wide)

    def test_no_platforms_detected(self):
        """Test behavior when no platforms are detected from user agent."""
        mac_platform = PlatformFactory(slug="mac", name="macOS")

        # Announcement with macOS platform
        mac_ann = AnnouncementFactory()
        mac_ann.platforms.add(mac_platform)

        # Site-wide announcement
        site_wide_ann = AnnouncementFactory()

        # Test with empty platform list (uncertainty case)
        announcements = Announcement._visible_query(platforms=[])
        self.assertEqual(2, announcements.count())
        self.assertIn(site_wide_ann, announcements)  # Site-wide included
        self.assertIn(mac_ann, announcements)  # macOS targeted included (uncertainty)

        # Test with None platforms (site-wide)
        announcements = Announcement.get_site_wide()
        self.assertEqual(2, announcements.count())
        self.assertIn(site_wide_ann, announcements)
        self.assertIn(mac_ann, announcements)
