import re

from django.forms import ValidationError
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.sumo.tests import TestCase
from kitsune.users.forms import ProfileForm
from kitsune.users.forms import username_allowed
from kitsune.users.tests import TestCaseBase
from kitsune.users.validators import TwitterValidator

FACEBOOK_URLS = (
    ('https://facebook.com/valid', True),
    ('http://www.facebook.com/valid', True),
    ('htt://facebook.com/invalid', False),
    ('http://notfacebook.com/invalid', False),
    ('http://facebook.com/', False),
)


class ProfileFormTestCase(TestCaseBase):
    form = ProfileForm()

    def setUp(self):
        self.form.cleaned_data = {}

    def test_facebook_pattern_attr(self):
        """Facebook field has the correct pattern attribute."""
        fragment = pq(self.form.as_ul())
        facebook = fragment('#id_facebook')[0]
        assert 'pattern' in facebook.attrib

        pattern = re.compile(facebook.attrib['pattern'])
        for url, match in FACEBOOK_URLS:
            eq_(bool(pattern.match(url)), match)

    def test_clean_facebook(self):
        clean = self.form.clean_facebook
        for url, match in FACEBOOK_URLS:
            self.form.cleaned_data['facebook'] = url
            if match:
                clean()  # Should not raise.
            else:
                self.assertRaises(ValidationError, clean)


class TwitterValidatorTestCase(TestCase):

    def setUp(self):

        def test_valid(self):
            TwitterValidator('a_valid_name')

        def test_has_number(self):
            TwitterValidator('valid123')

        def test_has_letter_number_underscore(self):
            TwitterValidator('valid_name_123')

    def test_has_slash(self):
        # Twitter usernames can not have slash "/"
        self.assertRaises(ValidationError, lambda: TwitterValidator('x/'))

    def test_has_at_sign(self):
        # Dont Accept Twitter Username with "@"
        self.assertRaises(ValidationError, lambda: TwitterValidator('@x'))


class Testusername_allowed(TestCase):
    def test_good_names(self):
        data = [
            ('ana', True),
            ('rlr', True),
            ('anal', False),
        ]

        for name, expected in data:
            eq_(username_allowed(name), expected)
