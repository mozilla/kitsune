from datetime import datetime, timedelta

from nose.tools import eq_

from kitsune.announcements.models import Announcement
from kitsune.announcements.tests import AnnouncementFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory, GroupFactory
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
        eq_(1, Announcement.get_site_wide().count())

    def test_always_visible(self):
        """Always visible announcements are shown."""
        # This one doesn't show
        AnnouncementFactory(show_after=datetime.now() + timedelta(days=2))
        AnnouncementFactory(
            show_after=datetime.now() - timedelta(days=2), content="stardate 43125"
        )

        site_wide = Announcement.get_site_wide()
        eq_(1, site_wide.count())
        eq_("stardate 43125", site_wide[0].content)

    def test_group_excluded(self):
        """Announcements in a group are not shown."""
        AnnouncementFactory(group=self.group)
        eq_(0, Announcement.get_site_wide().count())

    def test_get_for_group_id(self):
        """If no groups are passed, nothing is returned."""
        # Site-wide announcement
        AnnouncementFactory()
        # Announcement in a group.
        a = AnnouncementFactory(group=self.group)

        group_ann = Announcement.get_for_group_id(self.group.id)
        eq_(1, len(group_ann))
        eq_(a, group_ann[0])

    def test_get_for_locale_name(self):
        """Announcements for a specific locale are shown."""
        # Site-wide announcement
        AnnouncementFactory()
        # Announcement in a locale
        a = AnnouncementFactory(locale=self.locale)

        locale_ann = Announcement.get_for_locale_name(self.locale.locale)
        eq_(1, locale_ann.count())
        eq_(a, locale_ann[0])
