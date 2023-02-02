from django.conf import settings
from pyquery import PyQuery as pq

from kitsune.flagit.models import FlaggedObject
from kitsune.kbadge.tests import AwardFactory, BadgeFactory
from kitsune.questions.events import QuestionReplyEvent
from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.tests import get
from kitsune.sumo.urlresolvers import reverse
from kitsune.tidings.models import Watch
from kitsune.users.models import Profile
from kitsune.users.tests import TestCaseBase, UserFactory, add_permission
from kitsune.wiki.tests import RevisionFactory


class EditProfileTests(TestCaseBase):
    def test_edit_my_ProfileFactory(self):
        user = UserFactory()
        url = reverse("users.edit_my_profile")
        self.client.login(username=user.username, password="testpass")
        data = {
            "username": "jonh_doe",
            "name": "John Doe",
            "public_email": True,
            "bio": "my bio",
            "website": "http://google.com/",
            "twitter": "",
            "community_mozilla_org": "",
            "people_mozilla_org": "",
            "matrix_handle": "johndoe",
            "timezone": "America/New_York",
            "country": "US",
            "city": "Disney World",
            "locale": "en-US",
        }

        response = self.client.post(url, data)
        self.assertEqual(302, response.status_code)
        profile = Profile.objects.get(user=user)
        for key in data:
            if key not in ["timezone", "username"]:
                assert data[key] == getattr(profile, key), "%r != %r (for key '%s')" % (
                    data[key],
                    getattr(profile, key),
                    key,
                )

        self.assertEqual(data["timezone"], str(profile.timezone))
        self.assertEqual(data["username"], profile.user.username)

    def test_user_cant_edit_others_profile_without_permission(self):
        u1 = UserFactory()
        url = reverse("users.edit_profile", args=[u1.username])

        u2 = UserFactory()
        self.client.login(username=u2.username, password="testpass")

        # Try GET
        r = self.client.get(url)
        self.assertEqual(403, r.status_code)

        # Try POST
        r = self.client.post(url, {})
        self.assertEqual(403, r.status_code)

    def test_user_can_edit_others_profile_with_permission(self):
        user1 = UserFactory()
        url = reverse("users.edit_profile", args=[user1.username])

        user2 = UserFactory()
        add_permission(user2, Profile, "change_profile")
        self.client.login(username=user2.username, password="testpass")

        # Try GET
        resp = self.client.get(url)
        self.assertEqual(200, resp.status_code)

        # Try POST
        data = {
            "username": "jonh_doe",
            "name": "John Doe",
            "public_email": True,
            "bio": "my bio",
            "website": "http://google.com/",
            "twitter": "",
            "community_mozilla_org": "",
            "people_mozilla_org": "",
            "matrix_handle": "johndoe",
            "timezone": "America/New_York",
            "country": "US",
            "city": "Disney World",
            "locale": "en-US",
        }
        resp = self.client.post(url, data)
        self.assertEqual(302, resp.status_code)
        profile = Profile.objects.get(user=user1)
        for key in data:
            if key not in ["timezone", "username"]:
                assert data[key] == getattr(profile, key), "%r != %r (for key '%s')" % (
                    data[key],
                    getattr(profile, key),
                    key,
                )

        self.assertEqual(data["timezone"], str(profile.timezone))
        self.assertEqual(data["username"], profile.user.username)


class ViewProfileTests(TestCaseBase):
    def setUp(self):
        self.u = UserFactory(profile__name="", profile__website="")
        self.profile = self.u.profile

    def test_view_ProfileFactory(self):
        r = self.client.get(reverse("users.profile", args=[self.u.username]))
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(0, doc("#edit-profile-link").length)
        self.assertEqual(self.u.username, doc("h2.user").text())
        # No name set => no optional fields.
        self.assertEqual(0, doc(".contact").length)
        # Check canonical url
        self.assertEqual(
            "%s/en-US/user/%s/" % (settings.CANONICAL_URL, self.u.username),
            doc('link[rel="canonical"]')[0].attrib["href"],
        )

    def test_view_profile_mine(self):
        """Logged in, on my profile, I see an edit link."""
        self.client.login(username=self.u.username, password="testpass")
        r = self.client.get(reverse("users.profile", args=[self.u.username]))
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(
            1,
            len(doc(f"#user-nav li a[href='{reverse('users.edit_my_profile', locale='en-US')}']")),
        )
        self.client.logout()

    def test_bio_links_nofollow(self):
        self.profile.bio = "http://getseo.com, [http://getseo.com]"
        self.profile.save()
        r = self.client.get(reverse("users.profile", args=[self.u.username]))
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(2, len(doc('.bio a[rel="nofollow"]')))

    def test_bio_links_no_img(self):
        # bug 1427813
        self.profile.bio = '<p>my dude image <img src="https://www.example.com/the-dude.jpg"></p>'
        self.profile.save()
        r = self.client.get(reverse("users.profile", args=[self.u.username]))
        self.assertEqual(200, r.status_code)
        assert b"<p>my dude image </p>" in r.content

    def test_num_documents(self):
        """Verify the number of documents contributed by user."""
        u = UserFactory()
        RevisionFactory(creator=u)
        RevisionFactory(creator=u)

        r = self.client.get(reverse("users.profile", args=[u.username]))
        self.assertEqual(200, r.status_code)
        assert b"2 documents" in r.content

    def test_deactivate_button(self):
        """Check that the deactivate button is shown appropriately"""
        u = UserFactory()
        r = self.client.get(reverse("users.profile", args=[u.username]))
        assert b"Deactivate this user" not in r.content

        add_permission(self.u, Profile, "deactivate_users")
        self.client.login(username=self.u.username, password="testpass")
        r = self.client.get(reverse("users.profile", args=[u.username]))
        assert b"Deactivate this user" in r.content

        u.is_active = False
        u.save()
        r = self.client.get(reverse("users.profile", args=[u.username]))
        assert b"This user has been deactivated." in r.content

        r = self.client.get(reverse("users.profile", args=[self.u.username]))
        assert b"Deactivate this user" not in r.content

    def test_badges_listed(self):
        """Verify that awarded badges appear on the profile page."""
        badge_title = "awesomesauce badge"
        b = BadgeFactory(title=badge_title)
        u = UserFactory()
        AwardFactory(user=u, badge=b)
        r = self.client.get(reverse("users.profile", args=[u.username]))
        assert badge_title.encode() in r.content


class FlagProfileTests(TestCaseBase):
    def test_flagged_and_deleted_ProfileFactory(self):
        u = UserFactory()
        p = u.profile
        flag_user = UserFactory()
        # Flag a profile and delete it
        f = FlaggedObject(content_object=p, reason="spam", creator_id=flag_user.id)
        f.save()
        p.delete()

        # Verify flagit queue
        u = UserFactory()
        add_permission(u, FlaggedObject, "can_moderate")
        self.client.login(username=u.username, password="testpass")
        response = get(self.client, "flagit.queue")
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        self.assertEqual(1, len(doc("#flagged-queue form.update")))


class EditWatchListTests(TestCaseBase):
    """Test manage watch list"""

    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="testpass")

        self.question = QuestionFactory(creator=self.user)
        QuestionReplyEvent.notify(self.user, self.question)

    def test_GET(self):
        r = self.client.get(reverse("users.edit_watch_list"))
        self.assertEqual(200, r.status_code)
        assert "question: " + self.question.title in r.content.decode("utf8")

    def test_POST(self):
        w = Watch.objects.get(object_id=self.question.id, user=self.user)
        self.assertEqual(w.is_active, True)

        self.client.post(reverse("users.edit_watch_list"))
        w = Watch.objects.get(object_id=self.question.id, user=self.user)
        self.assertEqual(w.is_active, False)

        self.client.post(reverse("users.edit_watch_list"), {"watch_%s" % w.id: "1"})
        w = Watch.objects.get(object_id=self.question.id, user=self.user)
        self.assertEqual(w.is_active, True)
