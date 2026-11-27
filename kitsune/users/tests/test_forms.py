from django.forms import ValidationError

from kitsune.sumo.tests import TestCase
from kitsune.users.forms import username_allowed
from kitsune.users.validators import UsernameValidator, XUsernameValidator


class UsernameValidatorTestCase(TestCase):
    def test_valid_and_invalid_names(self):
        for name in ("a_valid_name", "valid123", "valid_name_123"):
            with self.subTest(name):
                UsernameValidator(name)
        for name in ("x/", "@x", "user-name", "/../../wp-login.php"):
            with self.subTest(name):
                self.assertRaises(ValidationError, UsernameValidator, name)


class XUsernameValidatorTestCase(TestCase):
    def test_accepts_usernames_and_profile_permalinks(self):
        for value in ("beedell_roke", "i/user/3782186368", "i/user/9223372036854775807"):
            XUsernameValidator(value)

    def test_rejects_invalid_profile_paths(self):
        for value in ("i/user/", "i/user/not-a-number", "users/123", "https://x.com/name"):
            with self.assertRaises(ValidationError):
                XUsernameValidator(value)


class Testusername_allowed(TestCase):
    def test_good_names(self):
        data = [
            ("ana", True),
            ("rlr", True),
            ("anal", False),
        ]

        for name, expected in data:
            self.assertEqual(username_allowed(name), expected)
