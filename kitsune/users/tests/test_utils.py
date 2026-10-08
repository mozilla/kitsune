from django.contrib.auth.models import User

from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory
from kitsune.users.utils import suggest_username


class UtilsTestCase(TestCase):
    def test_suggest_username(self):
        self.assertEqual("someuser", suggest_username("someuser@test.com"))

        User.objects.create(username="someuser")
        suggested = suggest_username("someuser@test.com")

        self.assertEqual("someuser1", suggested)

        User.objects.create(username="someuser4")
        suggested = suggest_username("someuser@test.com")
        self.assertEqual("someuser1", suggested)

        User.objects.create(username="ricky")
        User.objects.create(username="Ricky1")
        User.objects.create(username="ricky33")
        suggested = suggest_username("rIcky@test.com")
        self.assertEqual("rIcky2", suggested)

        User.objects.create(username="user")
        User.objects.create(username="user01")
        User.objects.create(username="user1")
        User.objects.create(username="user2")
        suggested = suggest_username("user@test.com")
        self.assertEqual("user3", suggested)

        User.objects.create(username="testuser+1")
        User.objects.create(username="testuser+11")
        suggested = suggest_username("testuser+1@example.com")
        self.assertEqual("testuser+12", suggested)

    def test_suggest_username_invalid_characters(self):
        """Test some invalid to Django usernames."""

        self.assertEqual("foobar", suggest_username("foo bar"))
        User.objects.create(username="foobar")
        self.assertEqual("foobar1", suggest_username("foo bar"))

        self.assertEqual("foobar1", suggest_username("foobar /1"))
        User.objects.create(username="foobar1")
        self.assertEqual("foobar11", suggest_username("foobar /1"))

    def test_suggest_username_reserves_hidden_system_usernames(self):
        UserFactory(username="hidden", profile__account_type=Profile.AccountType.SYSTEM)
        UserFactory(username="hidden1", profile__account_type=Profile.AccountType.SYSTEM)
        self.assertEqual("hidden2", suggest_username("hidden@example.com"))
