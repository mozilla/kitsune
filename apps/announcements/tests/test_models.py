from datetime import datetime, timedelta

from nose.tools import eq_

from announcements.models import Announcement
from announcements.tests import announcement
from sumo.tests import TestCase
from users.tests import user, group, profile
from wiki.tests import locale


class AnnouncementModelTests(TestCase):

    def setUp(self):
        super(AnnouncementModelTests, self).setUp()
        self.creator = user(save=True)
        profile(user=self.creator)
        self.group = group(save=True)
        self.locale = locale(locale='es', save=True)
        self.creator.groups.add(self.group)

    def test_active(self):
        """Active announcement shows."""
        announcement(show_after=datetime.now() - timedelta(days=2),
                     show_until=datetime.now() + timedelta(days=2)).save()
        eq_(1, Announcement.get_site_wide().count())

    def test_always_visible(self):
        """Always visible announcements are shown."""
        # This one doesn't show
        announcement(show_after=datetime.now() + timedelta(days=2)).save()
        announcement(show_after=datetime.now() - timedelta(days=2),
                     content='stardate 43125').save()

        site_wide = Announcement.get_site_wide()
        eq_(1, site_wide.count())
        eq_('stardate 43125', site_wide[0].content)

    def test_group_excluded(self):
        """Announcements in a group are not shown."""
        announcement(group=self.group).save()
        eq_(0, Announcement.get_site_wide().count())

    def test_get_for_group_id(self):
        """If no groups are passed, nothing is returned."""
        # Site-wide announcement
        announcement().save()
        # Announcement in a group.
        a = announcement(group=self.group, save=True)

        group_ann = Announcement.get_for_group_id(self.group.id)
        eq_(1, len(group_ann))
        eq_(a, group_ann[0])

    def test_get_for_locale_name(self):
        """Announcements for a specific locale are shown."""
        # Site-wide announcement
        announcement(save=True)
        # Announcement in a locale
        a = announcement(locale=self.locale, save=True)

        locale_ann = Announcement.get_for_locale_name(self.locale.locale)
        eq_(1, locale_ann.count())
        eq_(a, locale_ann[0])
