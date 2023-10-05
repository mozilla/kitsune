from pyquery import PyQuery as pq

from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory, add_permission
from kitsune.wiki.models import Locale
from kitsune.wiki.tests import LocaleFactory


class LocaleListTests(TestCase):
    def test_locale_list(self):
        """Verify the locale list renders all locales."""
        LocaleFactory(locale="en-US")
        LocaleFactory(locale="es")
        LocaleFactory(locale="de")

        r = self.client.get(reverse("wiki.locales"))
        self.assertEqual(r.status_code, 200)
        doc = pq(r.content)
        self.assertEqual(Locale.objects.count(), len(doc("#locale-listing li")))


class LocaleDetailsTests(TestCase):
    def test_locale_list(self):
        """Verify the locale list renders all locales."""
        lcl = LocaleFactory(locale="es")
        leader = UserFactory()
        lcl.leaders.add(leader)
        reviewer = UserFactory()
        lcl.reviewers.add(reviewer)
        editor = UserFactory()
        lcl.editors.add(editor)

        r = self.client.get(reverse("wiki.locale_details", args=[lcl.locale]))
        self.assertEqual(r.status_code, 200)
        doc = pq(r.content)
        leaders = doc("ul.leaders > li")
        self.assertEqual(1, len(leaders))
        assert leader.profile.name in leaders.text()
        reviewers = doc("ul.reviewers > li")
        self.assertEqual(1, len(reviewers))
        assert reviewer.profile.name in reviewers.text()
        editors = doc("ul.editors > li")
        self.assertEqual(1, len(editors))
        assert editor.profile.name in editors.text()


class AddRemoveLeaderTests(TestCase):
    def setUp(self):
        super(AddRemoveLeaderTests, self).setUp()
        self.locale = LocaleFactory(locale="es")
        self.user = UserFactory()
        add_permission(self.user, Locale, "change_locale")
        self.leader = UserFactory()
        self.client.login(username=self.user.username, password="testpass")

    def test_add_leader(self):
        url = reverse("wiki.add_locale_leader", args=[self.locale.locale])
        r = self.client.get(url)
        self.assertEqual(405, r.status_code)
        r = self.client.post(url, {"users": self.leader.username})
        self.assertEqual(302, r.status_code)
        assert self.leader in self.locale.leaders.all()

    def test_remove_leader(self):
        self.locale.leaders.add(self.leader)
        url = reverse("wiki.remove_locale_leader", args=[self.locale.locale, self.leader.id])
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        r = self.client.post(url)
        self.assertEqual(302, r.status_code)
        assert self.leader not in self.locale.leaders.all()


class AddRemoveReviewerTests(TestCase):
    def setUp(self):
        super(AddRemoveReviewerTests, self).setUp()
        self.locale = LocaleFactory(locale="es")
        self.user = UserFactory()
        self.locale.leaders.add(self.user)
        self.reviewer = UserFactory()
        self.client.login(username=self.user.username, password="testpass")

    def test_add_reviewer(self):
        url = reverse("wiki.add_locale_reviewer", args=[self.locale.locale])
        r = self.client.get(url)
        self.assertEqual(405, r.status_code)
        r = self.client.post(url, {"users": self.reviewer.username})
        self.assertEqual(302, r.status_code)
        assert self.reviewer in self.locale.reviewers.all()

    def test_remove_reviewer(self):
        self.locale.reviewers.add(self.reviewer)
        url = reverse("wiki.remove_locale_reviewer", args=[self.locale.locale, self.reviewer.id])
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        r = self.client.post(url)
        self.assertEqual(302, r.status_code)
        assert self.reviewer not in self.locale.reviewers.all()


class AddRemoveEditorTests(TestCase):
    def setUp(self):
        super(AddRemoveEditorTests, self).setUp()
        self.locale = LocaleFactory(locale="es")
        self.user = UserFactory()
        self.locale.leaders.add(self.user)
        self.editor = UserFactory()
        self.client.login(username=self.user.username, password="testpass")

    def test_add_editor(self):
        url = reverse("wiki.add_locale_editor", args=[self.locale.locale])
        r = self.client.get(url)
        self.assertEqual(405, r.status_code)
        r = self.client.post(url, {"users": self.editor.username})
        self.assertEqual(302, r.status_code)
        assert self.editor in self.locale.editors.all()

    def test_remove_editor(self):
        self.locale.editors.add(self.editor)
        url = reverse("wiki.remove_locale_editor", args=[self.locale.locale, self.editor.id])
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        r = self.client.post(url)
        self.assertEqual(302, r.status_code)
        assert self.editor not in self.locale.editors.all()
