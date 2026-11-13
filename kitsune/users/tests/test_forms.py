from django.forms import ValidationError

from kitsune.sumo.tests import TestCase
from kitsune.users.forms import username_allowed
from kitsune.users.validators import UsernameValidator, XUsernameValidator


class UsernameValidatorTestCase(TestCase):
    def setUp(self):
        def test_valid(self):
            UsernameValidator("a_valid_name")

        def test_has_number(self):
            UsernameValidator("valid123")

        def test_has_letter_number_underscore(self):
            UsernameValidator("valid_name_123")

    def test_has_slash(self):
        self.assertRaises(ValidationError, lambda: UsernameValidator("x/"))

    def test_has_at_sign(self):
        self.assertRaises(ValidationError, lambda: UsernameValidator("@x"))

    def test_has_hyphen(self):
        self.assertRaises(ValidationError, lambda: UsernameValidator("user-name"))

    def test_path_traversal_attack(self):
        self.assertRaises(ValidationError, lambda: UsernameValidator("/../../wp-login.php"))


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
