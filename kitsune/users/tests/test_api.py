import json
from datetime import timedelta
from http.cookies import SimpleCookie
from unittest import mock

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test.utils import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from kitsune.questions.tests import (
    AnswerFactory,
    AnswerVoteFactory,
    QuestionFactory,
    SolutionAnswerFactory,
)
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users import api
from kitsune.users.tests import GroupFactory, ProfileFactory, UserFactory


class UsernamesTests(TestCase):
    """Test the usernames API method."""

    url = reverse("users.api.usernames", locale="en-US")

    def setUp(self):
        self.u = UserFactory(username="testUser", profile__name="Ringo")
        self.client.login(username=self.u.username, password="testpass")

    def tearDown(self):
        self.client.logout()

    def test_no_query(self):
        res = self.client.get(self.url)
        self.assertEqual(200, res.status_code)
        self.assertEqual(b"[]", res.content)

    def test_query_old(self):
        res = self.client.get(urlparams(self.url, term="a"))
        self.assertEqual(200, res.status_code)
        data = json.loads(res.content)
        self.assertEqual(0, len(data))

    def test_query_current(self):
        # Test that we case-insensitively search the user's username.
        res = self.client.get(urlparams(self.url, term=self.u.username[0].upper()))
        self.assertEqual(200, res.status_code)
        data = json.loads(res.content)
        self.assertEqual(1, len(data))
        # Test that we also case-insensitively search the name of the user's profile.
        res = self.client.get(urlparams(self.url, term=self.u.profile.name.lower()))
        self.assertEqual(200, res.status_code)
        data = json.loads(res.content)
        self.assertEqual(1, len(data))

    def test_post(self):
        res = self.client.post(self.url)
        self.assertEqual(405, res.status_code)

    def test_logged_out(self):
        self.client.logout()
        res = self.client.get(self.url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(403, res.status_code)


class TestUserSerializer(TestCase):
    def setUp(self):
        self.request = mock.Mock()
        self.data = {
            "username": "bobb",
            "display_name": "Bobbert the Seventh",
            "password": "testpass",
            "email": "bobb@example.com",
        }

    def test_helpfulness(self):
        u = UserFactory()
        p = u.profile
        a1 = AnswerFactory(creator=u)
        a2 = AnswerFactory(creator=u)

        AnswerVoteFactory(answer=a1, helpful=True)
        AnswerVoteFactory(answer=a2, helpful=True)
        AnswerVoteFactory(answer=a2, helpful=True)
        # Some red herrings.
        AnswerVoteFactory(creator=u)
        AnswerVoteFactory(answer=a1, helpful=False)

        serializer = api.ProfileSerializer(instance=p)
        self.assertEqual(serializer.data["helpfulness"], 3)

    def test_counts(self):
        u = UserFactory()
        p = u.profile
        q = QuestionFactory(creator=u)
        AnswerFactory(creator=u)
        q.solution = AnswerFactory(question=q, creator=u)
        q.save()

        serializer = api.ProfileSerializer(instance=p)
        self.assertEqual(serializer.data["question_count"], 1)
        self.assertEqual(serializer.data["answer_count"], 2)
        self.assertEqual(serializer.data["solution_count"], 1)

    def test_last_answer_date(self):
        p = ProfileFactory()
        u = p.user
        AnswerFactory(creator=u)

        serializer = api.ProfileSerializer(instance=p)
        self.assertEqual(serializer.data["last_answer_date"], u.answers.last().created)


class TestUserView(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_usernames_with_periods(self):
        u = UserFactory(username="something.something")
        url = reverse("user-detail", args=[u.username])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["username"], u.username)

    def test_cant_delete(self):
        p = ProfileFactory()
        self.client.force_authenticate(user=p.user)
        url = reverse("user-detail", args=[p.user.username])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 405)

    def test_weekly_solutions(self):
        eight_days_ago = timezone.now() - timedelta(days=8)
        # First one is a solution, but it is too old.
        # second answer is not a solution.
        SolutionAnswerFactory(created=eight_days_ago)
        AnswerFactory()
        res = self.client.get(reverse("user-weekly-solutions"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 0)

        # Check that the data about the contributors is showing currectly
        user_info_list = []  # Info list with username and their number of solutions
        top_answer_number = 15
        for i in range(12):
            user = UserFactory()
            SolutionAnswerFactory.create_batch(top_answer_number, creator=user)
            user_info_list.append((user.username, top_answer_number))
            top_answer_number -= 1

        res = self.client.get(reverse("user-weekly-solutions"))
        self.assertEqual(res.status_code, 200)
        # Check only 10 users information is present there
        self.assertEqual(len(res.data), 10)
        # Create a list of the data with only the ``username`` and ``weekly_solutions``
        data_list = [(data["username"], data["weekly_solutions"]) for data in res.data]

        # Check only top 10 contributor information is in the API
        top_ten = user_info_list[:10]
        self.assertEqual(sorted(top_ten), sorted(data_list))

    def test_email_visible_when_signed_in(self):
        p = ProfileFactory()
        url = reverse("user-detail", args=[p.user.username])
        self.client.force_authenticate(user=p.user)
        res = self.client.get(url)
        self.assertEqual(res.data["email"], p.user.email)

    def test_email_not_visible_when_signed_out(self):
        p = ProfileFactory()
        url = reverse("user-detail", args=[p.user.username])
        res = self.client.get(url)
        assert "email" not in res.data

    def test_settings_visible_when_signed_in(self):
        p = ProfileFactory()
        p.settings.create(name="foo", value="bar")
        url = reverse("user-detail", args=[p.user.username])
        self.client.force_authenticate(user=p.user)
        res = self.client.get(url)
        self.assertEqual(res.data["settings"], [{"name": "foo", "value": "bar"}])

    def test_settings_not_visible_when_signed_out(self):
        p = ProfileFactory()
        p.settings.create(name="foo", value="bar")
        url = reverse("user-detail", args=[p.user.username])
        res = self.client.get(url)
        assert "settings" not in res.data

    def test_is_active(self):
        p = ProfileFactory()
        url = reverse("user-detail", args=[p.user.username])
        res = self.client.get(url)
        assert "is_active" in res.data


class TestUserCreation(TestCase):
    """Test the create_test_user API view."""

    url = reverse("users.api.create_test_user", locale="en-US")

    def setUp(self):
        GroupFactory(name="Group1")
        self.staff = GroupFactory(name="Staff")
        self.beatles = GroupFactory(name="Beatles")
        ct = ContentType.objects.get_for_model(User)
        self.perm1 = Permission.objects.get_or_create(
            name="p1", codename="perm1", content_type=ct
        )[0]
        self.perm2 = Permission.objects.get_or_create(
            name="p2", codename="perm2", content_type=ct
        )[0]
        Permission.objects.get_or_create(name="p3", codename="perm3", content_type=ct)
        ringo = UserFactory(username="ringo", groups=[self.staff, self.beatles])
        self.client.logout()
        self.client.login(username=ringo.username, password="testpass")

    @override_settings(DEV=True, ENABLE_TESTING_ENDPOINTS=True)
    def test_create_test_user(self):
        response = self.client.post(
            self.url,
            content_type="application/json",
            data={
                "username": "mccartney",
                "groups": ["Staff", "Beatles"],
                "permissions": ["perm1", "perm2"],
            },
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["username"], "mccartney")
        self.assertIn("cookies", result)
        self.assertTrue(result["cookies"])
        mccartney_session_cookie = result["cookies"][0]
        for key in (
            "name",
            "value",
            "max-age",
            "path",
            "domain",
            "secure",
            "httponly",
            "samesite",
        ):
            self.assertIn(key, mccartney_session_cookie)

        user = User.objects.get(username="mccartney")

        self.assertEqual({g.name for g in user.groups.all()}, {"Staff", "Beatles"})  # noqa: group-leak
        self.assertEqual(
            {p.codename for p in user.user_permissions.all()}, {"perm1", "perm2"}
        )

        self.client.logout()

        # Test McCartney's session cookie to ensure it's good.
        cookie = SimpleCookie()
        cookie[mccartney_session_cookie["name"]] = mccartney_session_cookie["value"]
        morsel = cookie[mccartney_session_cookie["name"]]
        for key in ("max-age", "path", "domain", "secure", "httponly", "samesite"):
            morsel[key] = mccartney_session_cookie[key]
        response = self.client.post(
            self.url,
            content_type="application/json",
            headers={"cookie": cookie.output(header="").strip()},
            data={"username": "lennon", "permissions": ["perm1"], "groups": ["Beatles"]},
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["username"], "lennon")
        self.assertIn("cookies", result)

        user = User.objects.get(username="lennon")

        self.assertEqual([g.name for g in user.groups.all()], ["Beatles"])  # noqa: group-leak
        self.assertEqual([p.codename for p in user.user_permissions.all()], ["perm1"])

    def test_create_test_user_404(self):
        """
        Test all of the 404 cases for the create-test-user endpoint.
        """
        with (
            self.subTest("not enabled"),
            override_settings(DEV=True, ENABLE_TESTING_ENDPOINTS=False),
        ):
            response = self.client.post(
                self.url,
                content_type="application/json",
                data={
                    "username": "mccartney",
                    "groups": ["Staff", "Beatles"],
                    "permissions": ["perm1", "perm2"],
                },
            )
            self.assertEqual(response.status_code, 404)

        with (
            self.subTest("not authenticated"),
            override_settings(DEV=True, ENABLE_TESTING_ENDPOINTS=True),
        ):
            self.client.logout()
            response = self.client.post(
                self.url,
                content_type="application/json",
                data={
                    "username": "mccartney",
                    "groups": ["Staff", "Beatles"],
                    "permissions": ["perm1", "perm2"],
                },
            )
            self.assertEqual(response.status_code, 404)

        with (
            self.subTest("not staff"),
            override_settings(DEV=True, ENABLE_TESTING_ENDPOINTS=True),
        ):
            self.client.logout()
            george = UserFactory(username="george", groups=[self.beatles])
            self.client.login(username=george.username, password="testpass")
            response = self.client.post(
                self.url,
                content_type="application/json",
                data={
                    "username": "mccartney",
                    "groups": ["Staff", "Beatles"],
                    "permissions": ["perm1", "perm2"],
                },
            )
            self.assertEqual(response.status_code, 404)

    @override_settings(DEV=True, ENABLE_TESTING_ENDPOINTS=True)
    def test_create_test_user_409(self):
        """
        Test when trying to create a user that already exists.
        """
        UserFactory(username="mccartney")
        response = self.client.post(
            self.url,
            content_type="application/json",
            data={"username": "mccartney"},
        )
        self.assertEqual(response.status_code, 409)

class TestUserDeletion(TestCase):
    """Test the trigger-delete API."""

    url = reverse("users.api.trigger_delete", locale="en-US")

    def setUp(self):
        GroupFactory(name="Group1")
        self.staff = GroupFactory(name="Staff")
        self.beatles = GroupFactory(name="Beatles")
        ringo = UserFactory(username="ringo", groups=[self.staff, self.beatles])
        self.james = UserFactory(username="james1")
        self.james2 = UserFactory(username="james2")
        self.client.logout()
        self.client.login(username=ringo.username, password="testpass")

    @override_settings(DEV=True, ENABLE_TESTING_ENDPOINTS=True)
    def test_delete_test_user(self):
        """Test correct user is deleted."""
        response = self.client.post(
            self.url,
            content_type="application/json",
            data={"username": self.james.username}
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["message"], f"{self.james.username} was successfully deleted!")
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username=self.james.username)

    @override_settings(DEV=True, ENABLE_TESTING_ENDPOINTS=True)
    def test_delete_non_existent_user(self):
        """Test when trying to delete a user that does not exist."""
        jmg = "jamesmcgill"
        response = self.client.post(
            self.url,
            content_type="application/json",
            data={"username": jmg}
        )
        result = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(result["message"], f"{jmg} does not exist.")

    def test_delete_test_user_404(self):
        """
        Test all cases in which the user doesn't have the necessary perms to hit the endpoint.
        """
        with (
            self.subTest("not enabled"),
            override_settings(DEV=True, ENABLE_TESTING_ENDPOINTS=False),
        ):
            response = self.client.post(
                self.url,
                content_type="application/json",
                data={"username": self.james2.username}
            )
            self.assertEqual(response.status_code, 404)

        with (
            self.subTest("not authenticated"),
            override_settings(DEV=True, ENABLE_TESTING_ENDPOINTS=True),
        ):
            self.client.logout()
            response = self.client.post(
                self.url,
                content_type="application/json",
                data={"username": self.james2.username}
            )
            self.assertEqual(response.status_code, 404)

        with (
            self.subTest("not staff"),
            override_settings(DEV=True, ENABLE_TESTING_ENDPOINTS=True),
        ):
            self.client.logout()
            michael = UserFactory(username="michael", groups=[self.beatles])
            self.client.login(username=michael.username, password="testpass")
            response = self.client.post(
                self.url,
                content_type="application/json",
                data={"username": self.james2.username}
            )
            self.assertEqual(response.status_code, 404)
