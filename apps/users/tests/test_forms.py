import re

from django.contrib.auth.models import User
from django.forms import ValidationError

from nose.tools import eq_
from pyquery import PyQuery as pq

from users.forms import (AuthenticationForm, ProfileForm, RegisterForm,
                         SetPasswordForm)
from users.tests import TestCaseBase, user


class AuthenticationFormTests(TestCaseBase):
    """AuthenticationForm tests."""
    fixtures = ['users.json']

    def test_only_active(self):
        # Verify with active user
        u = User.objects.get(username='rrosario')
        assert u.is_active
        form = AuthenticationForm(data={'username': 'rrosario',
                                        'password': 'testpass'})
        assert form.is_valid()

        # Verify with inactive user
        u.is_active = False
        u.save()
        u = User.objects.get(username='rrosario')
        assert not u.is_active
        form = AuthenticationForm(data={'username': 'rrosario',
                                        'password': 'testpass'})
        assert not form.is_valid()

    def test_allow_inactive(self):
        # Verify with active user
        u = User.objects.get(username='rrosario')
        assert u.is_active
        form = AuthenticationForm(only_active=False,
                                  data={'username': 'rrosario',
                                        'password': 'testpass'})
        assert form.is_valid()

        # Verify with inactive user
        u.is_active = False
        u.save()
        u = User.objects.get(username='rrosario')
        assert not u.is_active
        form = AuthenticationForm(only_active=False,
                                  data={'username': 'rrosario',
                                        'password': 'testpass'})
        assert form.is_valid()


FACEBOOK_URLS = (
    ('https://facebook.com/valid', True),
    ('http://www.facebook.com/valid', True),
    ('htt://facebook.com/invalid', False),
    ('http://notfacebook.com/invalid', False),
    ('http://facebook.com/', False),
)

TWITTER_URLS = (
    ('https://twitter.com/valid', True),
    ('http://www.twitter.com/valid', True),
    ('htt://twitter.com/invalid', False),
    ('http://nottwitter.com/invalid', False),
    ('http://twitter.com/', False),
)


class ProfileFormTestCase(TestCaseBase):
    fixtures = ['users.json']
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

    def test_twitter_pattern_attr(self):
        """Twitter field has the correct pattern attribute."""
        fragment = pq(self.form.as_ul())
        twitter = fragment('#id_twitter')[0]
        assert 'pattern' in twitter.attrib

        pattern = re.compile(twitter.attrib['pattern'])
        for url, match in TWITTER_URLS:
            eq_(bool(pattern.match(url)), match)

    def test_clean_facebook(self):
        clean = lambda: self.form.clean_facebook()
        for url, match in FACEBOOK_URLS:
            self.form.cleaned_data['facebook'] = url
            if match:
                clean()  # Should not raise.
            else:
                self.assertRaises(ValidationError, clean)

    def test_clean_twitter(self):
        clean = lambda: self.form.clean_twitter()
        for url, match in TWITTER_URLS:
            self.form.cleaned_data['twitter'] = url
            if match:
                clean()  # Should not raise.
            else:
                self.assertRaises(ValidationError, clean)


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
                             'password': 'fksjvaj',
                             'password2': 'fksjvaj',
                             'email': 'newuser@example.com'})
        assert form.is_valid()

    def test_bad_username(self):
        #  Simple match.
        form = RegisterForm({'username': 'ass',
                             'password': 'adssadfsadf',
                             'password2': 'adssadfsadf',
                             'email': 'newuser@example.com'})
        assert not form.is_valid()
        # Simple obfuscation.
        form = RegisterForm({'username': 'a.s.s',
                             'password': 'adssadfsadf',
                             'password2': 'adssadfsadf',
                             'email': 'newuser@example.com'})
        assert not form.is_valid()
        # Partial match.
        form = RegisterForm({'username': 'ass.assassin',
                             'password': 'adssadfsadf',
                             'password2': 'adssadfsadf',
                             'email': 'newuser@example.com'})
        assert not form.is_valid()
        # No match.
        form = RegisterForm({'username': 'assassin',
                             'password': 'adssadfsadf',
                             'password2': 'adssadfsadf',
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
