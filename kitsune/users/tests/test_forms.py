from django.forms import ValidationError

from kitsune.sumo.tests import TestCase
from kitsune.users.forms import username_allowed
from kitsune.users.validators import TwitterValidator


class TwitterValidatorTestCase(TestCase):
    def setUp(self):
        def test_valid(self):
            TwitterValidator("a_valid_name")

        def test_has_number(self):
            TwitterValidator("valid123")

        def test_has_letter_number_underscore(self):
            TwitterValidator("valid_name_123")

    def test_has_slash(self):
        # Twitter usernames can not have slash "/"
        self.assertRaises(ValidationError, lambda: TwitterValidator("x/"))

    def test_has_at_sign(self):
        # Dont Accept Twitter Username with "@"
        self.assertRaises(ValidationError, lambda: TwitterValidator("@x"))


class Testusername_allowed(TestCase):
    def test_good_names(self):
        data = [
            ("ana", True),
            ("rlr", True),
            ("anal", False),
        ]

        for name, expected in data:
            self.assertEqual(username_allowed(name), expected)
