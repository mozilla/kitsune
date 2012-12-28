from datetime import datetime

from nose.tools import eq_

from announcements.models import Announcement
from announcements.tests import announcement
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from users.tests import user
from wiki.tests import locale


class TestCreateLocaleAnnouncement(TestCase):

    def setUp(self):
        self.locale1 = locale(save=True)
        self.locale2 = locale(save=True, locale='es')

        self.u1 = user(save=True)
        self.u2 = user(save=True)
        self.u3 = user(save=True)

        self.u1.is_superuser = 1
        self.u1.save()

        self.locale1.leaders.add(self.u2)
        self.locale1.save()

        self.locale2.leaders.add(self.u3)
        self.locale2.save()

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
        self.client.login(username=self.u1.username, password='testpass')
        self._create_test(200, 1)

    def test_leader(self):
        self.client.login(username=self.u3.username, password='testpass')
        self._create_test(200, 1)

    def test_no_perms(self):
        self.client.login(username=self.u2.username, password='testpass')
        self._create_test(403, 0)

    def test_anon(self):
        self._create_test(302, 0)


class TestDeleteAnnouncement(TestCase):

    def setUp(self):
        self.locale1 = locale(save=True)
        self.locale2 = locale(save=True, locale='es')

        self.u1 = user(save=True)
        self.u2 = user(save=True)
        self.u3 = user(save=True)

        self.u1.is_superuser = 1
        self.u1.save()

        self.locale1.leaders.add(self.u2)
        self.locale1.save()

        self.locale2.leaders.add(self.u3)
        self.locale2.save()

        self.announcement = announcement(save=True, creator=self.u2,
            locale=self.locale2, content="Look at me!",
            show_after=datetime(2012, 01, 01, 0, 0, 0))

    def _delete_test(self, id, status, count):
        """Login, or other setup, then call this."""
        url = reverse('announcements.delete', locale='es', args=(id,))
        resp = self.client.post(url)
        eq_(resp.status_code, status)
        eq_(Announcement.objects.count(), count)

    def test_delete(self):
        self.client.login(username=self.u1.username, password='testpass')
        self._delete_test(self.announcement.id, 204, 0)

    def test_leader(self):
        self.client.login(username=self.u3.username, password='testpass')
        self._delete_test(self.announcement.id, 204, 0)

    def test_no_perms(self):
        self.client.login(username=self.u2.username, password='testpass')
        self._delete_test(self.announcement.id, 403, 1)

    def test_anon(self):
        self._delete_test(self.announcement.id, 302, 1)
