from datetime import datetime

from kitsune.announcements.models import Announcement
from kitsune.announcements.tests import AnnouncementFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory, add_permission
from kitsune.wiki.tests import LocaleFactory


class TestCreateLocaleAnnouncement(TestCase):
    def setUp(self):
        self.locale = LocaleFactory(locale="es")

    def _create_test(self, status, count):
        """Login, or other setup, then call this."""
        url = reverse("announcements.create_for_locale", locale="es")
        resp = self.client.post(
            url,
            {
                "content": "Look at me!",
                "show_after": "2012-01-01",
            },
        )
        self.assertEqual(resp.status_code, status)
        self.assertEqual(Announcement.objects.count(), count)

    def test_create(self):
        u = UserFactory(is_superuser=1)
        self.client.login(username=u.username, password="testpass")
        self._create_test(200, 1)

    def test_leader(self):
        u = UserFactory()
        self.locale.leaders.add(u)
        self.locale.save()
        self.client.login(username=u.username, password="testpass")
        self._create_test(200, 1)

    def test_has_permission(self):
        u = UserFactory()
        add_permission(u, Announcement, "add_announcement")
        self.client.login(username=u.username, password="testpass")
        self._create_test(200, 1)

    def test_no_perms(self):
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        self._create_test(403, 0)

    def test_anon(self):
        self._create_test(302, 0)


class TestDeleteAnnouncement(TestCase):
    def setUp(self):
        self.locale = LocaleFactory(locale="es")

        self.u = UserFactory()

        self.locale.leaders.add(self.u)
        self.locale.save()

        self.announcement = AnnouncementFactory(
            creator=self.u,
            locale=self.locale,
            content="Look at me!",
            show_after=datetime(2012, 1, 1, 0, 0, 0),
        )

    def _delete_test(self, id, status, count):
        """Login, or other setup, then call this."""
        url = reverse("announcements.delete", locale="es", args=(id,))
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status)
        self.assertEqual(Announcement.objects.count(), count)

    def test_delete(self):
        u = UserFactory(is_superuser=1)
        self.client.login(username=u.username, password="testpass")
        self._delete_test(self.announcement.id, 204, 0)

    def test_leader(self):
        # Use the user that was created in setUp.
        self.client.login(username=self.u.username, password="testpass")
        self._delete_test(self.announcement.id, 204, 0)

    def test_has_permission(self):
        u = UserFactory()
        add_permission(u, Announcement, "add_announcement")
        self.client.login(username=u.username, password="testpass")
        self._delete_test(self.announcement.id, 204, 0)

    def test_no_perms(self):
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        self._delete_test(self.announcement.id, 403, 1)

    def test_anon(self):
        self._delete_test(self.announcement.id, 302, 1)
