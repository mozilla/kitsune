import re
from django.forms import ValidationError

from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.users.forms import (
    AuthenticationForm, ProfileForm, RegisterForm, SetPasswordForm,
    ForgotUsernameForm, username_allowed)
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import TestCaseBase, user
from kitsune.users.validators import TwitterValidator


class AuthenticationFormTests(TestCaseBase):
    """AuthenticationForm tests."""

    def setUp(self):
        # create active and inactive users
        self.active_user = user(save=True,
                                username='activeuser',
                                is_active=True)

        self.inactive_user = user(save=True,
                                  username='inactiveuser',
                                  is_active=False)

    def test_only_active(self):
        # Verify with active user
        form = AuthenticationForm(data={'username': self.active_user.username,
                                        'password': 'testpass'})
        assert form.is_valid()

        # Verify with inactive user
        form = AuthenticationForm(data={
            'username': self.inactive_user.username,
            'password': 'testpass'})
        assert not form.is_valid()

    def test_allow_inactive(self):
        # Verify with active user
        form = AuthenticationForm(only_active=False,
                                  data={'username': self.active_user.username,
                                        'password': 'testpass'})
        assert form.is_valid()

        # Verify with inactive user
        form = AuthenticationForm(only_active=False, data={
            'username': self.inactive_user.username,
            'password': 'testpass'})
        assert form.is_valid()

    def test_at_in_username(self):
        u = user(username='test@example.com', save=True)
        form = AuthenticationForm(data={'username': u.username,
                                        'password': 'testpass'})
        assert form.is_valid()


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


class RegisterFormTests(TestCaseBase):
    """RegisterForm tests."""

    def test_common_password(self):
        form = RegisterForm({'username': 'newuser',
                             'password': 'password',
                             'password2': 'password',
                             'email': 'newuser@example.com'})
        assert not form.is_valid()

    def test_strong_password(self):
        form = RegisterForm({'username': 'newuser',
                             'password': 'fksjvaj1',
                             'password2': 'fksjvaj1',
                             'email': 'newuser@example.com'})
        assert form.is_valid()

    def test_bad_username(self):
        #  Simple match.
        form = RegisterForm({'username': 'ass',
                             'password': 'adssadfsadf1',
                             'password2': 'adssadfsadf1',
                             'email': 'newuser@example.com'})
        assert not form.is_valid()
        # Simple obfuscation.
        form = RegisterForm({'username': 'a.s.s',
                             'password': 'adssadfsadf1',
                             'password2': 'adssadfsadf1',
                             'email': 'newuser@example.com'})
        assert not form.is_valid()
        # Partial match.
        form = RegisterForm({'username': 'ass.assassin',
                             'password': 'adssadfsadf1',
                             'password2': 'adssadfsadf1',
                             'email': 'newuser@example.com'})
        assert not form.is_valid()
        # Plus sign
        form = RegisterForm({'username': 'ass+assin',
                             'password': 'adssadfsadf1',
                             'password2': 'adssadfsadf1',
                             'email': 'newuser@example.com'})
        assert not form.is_valid()
        # No match.
        form = RegisterForm({'username': 'assassin',
                             'password': 'adssadfsadf1',
                             'password2': 'adssadfsadf1',
                             'email': 'newuser@example.com'})
        assert form.is_valid()


class SetPasswordFormTests(TestCaseBase):
    """SetPasswordForm tests."""

    def test_common_password(self):
        form = SetPasswordForm(None, data={'new_password1': 'password',
                                           'new_password2': 'password'})
        assert not form.is_valid()


class PasswordChangeFormFormTests(TestCaseBase):
    """PasswordChangeForm tests."""

    def test_common_password(self):
        u = user(save=True)
        form = SetPasswordForm(u, data={'new_password1': 'password',
                                        'new_password2': 'password',
                                        'old_password': 'testpass'})
        assert not form.is_valid()


class ForgotUsernameFormTests(TestCaseBase):
    """ForgotUsernameForm tests."""

    def test_email_doesnt_exist(self):
        """If no account with email exists, form isn't valid."""
        form = ForgotUsernameForm({'email': 'a@b.com'})
        assert not form.is_valid()

    def test_valid_email(self):
        """"If an account with email exists, form is valid."""
        u = user(save=True, email='a@b.com', is_active=True)
        form = ForgotUsernameForm({'email': u.email})
        assert form.is_valid()


class Testusername_allowed(TestCase):
    def test_good_names(self):
        data = [
            ('ana', True),
            ('rlr', True),
            ('anal', False),
        ]

        for name, expected in data:
            eq_(username_allowed(name), expected)
