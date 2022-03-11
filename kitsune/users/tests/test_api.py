import json
from datetime import datetime, timedelta
from unittest import mock

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
from kitsune.users.tests import ProfileFactory, UserFactory


class UsernamesTests(TestCase):
    """Test the usernames API method."""

    url = reverse("users.api.usernames", locale="en-US")

    def setUp(self):
        self.u = UserFactory(username="testUser")
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
        res = self.client.get(urlparams(self.url, term=self.u.username[0]))
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
        eight_days_ago = datetime.now() - timedelta(days=8)
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

    def test_avatar_size(self):
        p = ProfileFactory()
        url = reverse("user-detail", args=[p.user.username])

        res = self.client.get(url)
        assert "?s=200" in res.data["avatar"]

        res = self.client.get(url, {"avatar_size": 128})
        assert "?s=128" in res.data["avatar"]
