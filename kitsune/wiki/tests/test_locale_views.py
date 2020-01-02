from nose.tools import eq_

from pyquery import PyQuery as pq

from kitsune.sumo.tests import TestCase, LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory, add_permission
from kitsune.wiki.models import Locale
from kitsune.wiki.tests import LocaleFactory


class LocaleListTests(TestCase):
    client_class = LocalizingClient

    def test_locale_list(self):
        """Verify the locale list renders all locales."""
        LocaleFactory(locale="en-US")
        LocaleFactory(locale="es")
        LocaleFactory(locale="de")

        r = self.client.get(reverse("wiki.locales"))
        eq_(r.status_code, 200)
        doc = pq(r.content)
        eq_(Locale.objects.count(), len(doc("#locale-listing li")))


class LocaleDetailsTests(TestCase):
    client_class = LocalizingClient

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
        eq_(r.status_code, 200)
        doc = pq(r.content)
        leaders = doc("ul.leaders > li")
        eq_(1, len(leaders))
        assert leader.profile.name in leaders.text()
        reviewers = doc("ul.reviewers > li")
        eq_(1, len(reviewers))
        assert reviewer.profile.name in reviewers.text()
        editors = doc("ul.editors > li")
        eq_(1, len(editors))
        assert editor.profile.name in editors.text()


class AddRemoveLeaderTests(TestCase):
    client_class = LocalizingClient

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
        eq_(405, r.status_code)
        r = self.client.post(url, {"users": self.leader.username})
        eq_(302, r.status_code)
        assert self.leader in self.locale.leaders.all()

    def test_remove_leader(self):
        self.locale.leaders.add(self.leader)
        url = reverse(
            "wiki.remove_locale_leader", args=[self.locale.locale, self.leader.id]
        )
        r = self.client.get(url)
        eq_(200, r.status_code)
        r = self.client.post(url)
        eq_(302, r.status_code)
        assert self.leader not in self.locale.leaders.all()


class AddRemoveReviewerTests(TestCase):
    client_class = LocalizingClient

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
        eq_(405, r.status_code)
        r = self.client.post(url, {"users": self.reviewer.username})
        eq_(302, r.status_code)
        assert self.reviewer in self.locale.reviewers.all()

    def test_remove_reviewer(self):
        self.locale.reviewers.add(self.reviewer)
        url = reverse(
            "wiki.remove_locale_reviewer", args=[self.locale.locale, self.reviewer.id]
        )
        r = self.client.get(url)
        eq_(200, r.status_code)
        r = self.client.post(url)
        eq_(302, r.status_code)
        assert self.reviewer not in self.locale.reviewers.all()


class AddRemoveEditorTests(TestCase):
    client_class = LocalizingClient

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
        eq_(405, r.status_code)
        r = self.client.post(url, {"users": self.editor.username})
        eq_(302, r.status_code)
        assert self.editor in self.locale.editors.all()

    def test_remove_editor(self):
        self.locale.editors.add(self.editor)
        url = reverse(
            "wiki.remove_locale_editor", args=[self.locale.locale, self.editor.id]
        )
        r = self.client.get(url)
        eq_(200, r.status_code)
        r = self.client.post(url)
        eq_(302, r.status_code)
        assert self.editor not in self.locale.editors.all()
