from datetime import datetime

from nose.tools import eq_

from announcements.models import Announcement
from announcements.tests import announcement
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from users.tests import user, add_permission
from wiki.tests import locale


class TestCreateLocaleAnnouncement(TestCase):

    def setUp(self):
        self.locale = locale(save=True, locale='es')

    def _create_test(self, status, count):
        """Login, or other setup, then call this."""
        url = reverse('announcements.create_for_locale', locale='es')
        resp = self.client.post(url, {
            'content': 'Look at me!',
            'show_after': '2012-01-01',
        })
        eq_(resp.status_code, status)
        eq_(Announcement.objects.count(), count)

    def test_create(self):
        u = user(save=True, is_superuser=1)
        self.client.login(username=u.username, password='testpass')
        self._create_test(200, 1)

    def test_leader(self):
        u = user(save=True)
        self.locale.leaders.add(u)
        self.locale.save()
        self.client.login(username=u.username, password='testpass')
        self._create_test(200, 1)

    def test_has_permission(self):
        u = user(save=True)
        add_permission(u, Announcement, 'add_announcement')
        self.client.login(username=u.username, password='testpass')
        self._create_test(200, 1)

    def test_no_perms(self):
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')
        self._create_test(403, 0)

    def test_anon(self):
        self._create_test(302, 0)


class TestDeleteAnnouncement(TestCase):

    def setUp(self):
        self.locale = locale(save=True, locale='es')

        self.u = user(save=True)

        self.locale.leaders.add(self.u)
        self.locale.save()

        self.announcement = announcement(save=True, creator=self.u,
            locale=self.locale, content="Look at me!",
            show_after=datetime(2012, 01, 01, 0, 0, 0))

    def _delete_test(self, id, status, count):
        """Login, or other setup, then call this."""
        url = reverse('announcements.delete', locale='es', args=(id,))
        resp = self.client.post(url)
        eq_(resp.status_code, status)
        eq_(Announcement.objects.count(), count)

    def test_delete(self):
        u = user(save=True, is_superuser=1)
        self.client.login(username=u.username, password='testpass')
        self._delete_test(self.announcement.id, 204, 0)

    def test_leader(self):
        # Use the user that was created in setUp.
        self.client.login(username=self.u.username, password='testpass')
        self._delete_test(self.announcement.id, 204, 0)

    def test_has_permission(self):
        u = user(save=True)
        add_permission(u, Announcement, 'add_announcement')
        self.client.login(username=u.username, password='testpass')
        self._delete_test(self.announcement.id, 204, 0)

    def test_no_perms(self):
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')
        self._delete_test(self.announcement.id, 403, 1)

    def test_anon(self):
        self._delete_test(self.announcement.id, 302, 1)
