from django.contrib.auth.models import User
from nose.tools import eq_

from kitsune.sumo.tests import TestCase
from kitsune.users.utils import suggest_username


class UtilsTestCase(TestCase):
    def test_suggest_username(self):
        eq_("someuser", suggest_username("someuser@test.com"))

        User.objects.create(username="someuser")
        suggested = suggest_username("someuser@test.com")

        eq_("someuser1", suggested)

        User.objects.create(username="someuser4")
        suggested = suggest_username("someuser@test.com")
        eq_("someuser1", suggested)

        User.objects.create(username="ricky")
        User.objects.create(username="Ricky1")
        User.objects.create(username="ricky33")
        suggested = suggest_username("rIcky@test.com")
        eq_("rIcky2", suggested)

        User.objects.create(username="user")
        User.objects.create(username="user01")
        User.objects.create(username="user1")
        User.objects.create(username="user2")
        suggested = suggest_username("user@test.com")
        eq_("user3", suggested)

        User.objects.create(username="testuser+1")
        User.objects.create(username="testuser+11")
        suggested = suggest_username("testuser+1@example.com")
        eq_("testuser+12", suggested)

    def test_suggest_username_invalid_characters(self):
        """Test some invalid to Django usernames."""

        eq_("foobar", suggest_username("foo bar"))
        User.objects.create(username="foobar")
        eq_("foobar1", suggest_username("foo bar"))

        eq_("foobar1", suggest_username("foobar /1"))
        User.objects.create(username="foobar1")
        eq_("foobar11", suggest_username("foobar /1"))
