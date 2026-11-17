from django.forms import ValidationError

from kitsune.sumo.tests import TestCase
from kitsune.users.forms import username_allowed
from kitsune.users.validators import UsernameValidator


class UsernameValidatorTestCase(TestCase):
    def test_valid_and_invalid_names(self):
        for name in ("a_valid_name", "valid123", "valid_name_123"):
            with self.subTest(name):
                UsernameValidator(name)
        for name in ("x/", "@x", "user-name", "/../../wp-login.php"):
            with self.subTest(name):
                self.assertRaises(ValidationError, UsernameValidator, name)


class Testusername_allowed(TestCase):
    def test_good_names(self):
        data = [
            ("ana", True),
            ("rlr", True),
            ("anal", False),
        ]

        for name, expected in data:
            self.assertEqual(username_allowed(name), expected)
