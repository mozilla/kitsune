import re
from django.forms import ValidationError

from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.users.forms import (
    AuthenticationForm,
    ProfileForm,
    SetPasswordForm,
    ForgotUsernameForm,
    username_allowed,
)
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import TestCaseBase, UserFactory
from kitsune.users.validators import TwitterValidator


class AuthenticationFormTests(TestCaseBase):
    """AuthenticationForm tests."""

    def setUp(self):
        # create active and inactive users
        self.active_user = UserFactory(username="activeuser", is_active=True)
        self.inactive_user = UserFactory(username="inactiveuser", is_active=False)

    def test_only_active(self):
        # Verify with active user
        form = AuthenticationForm(
            data={"username": self.active_user.username, "password": "testpass"}
        )
        assert form.is_valid()

        # Verify with inactive user
        form = AuthenticationForm(
            data={"username": self.inactive_user.username, "password": "testpass"}
        )
        assert not form.is_valid()

    def test_allow_inactive(self):
        # Verify with active user
        form = AuthenticationForm(
            only_active=False,
            data={"username": self.active_user.username, "password": "testpass"},
        )
        assert form.is_valid()

        # Verify with inactive user
        form = AuthenticationForm(
            only_active=False,
            data={"username": self.inactive_user.username, "password": "testpass"},
        )
        assert form.is_valid()

    def test_at_in_username(self):
        u = UserFactory(username="test@example.com")
        form = AuthenticationForm(data={"username": u.username, "password": "testpass"})
        assert form.is_valid()


FACEBOOK_URLS = (
    ("https://facebook.com/valid", True),
    ("http://www.facebook.com/valid", True),
    ("htt://facebook.com/invalid", False),
    ("http://notfacebook.com/invalid", False),
    ("http://facebook.com/", False),
)


class ProfileFormTestCase(TestCaseBase):
    form = ProfileForm()

    def setUp(self):
        self.form.cleaned_data = {}

    def test_facebook_pattern_attr(self):
        """Facebook field has the correct pattern attribute."""
        fragment = pq(self.form.as_ul())
        facebook = fragment("#id_facebook")[0]
        assert "pattern" in facebook.attrib

        pattern = re.compile(facebook.attrib["pattern"])
        for url, match in FACEBOOK_URLS:
            eq_(bool(pattern.match(url)), match)

    def test_clean_facebook(self):
        clean = self.form.clean_facebook
        for url, match in FACEBOOK_URLS:
            self.form.cleaned_data["facebook"] = url
            if match:
                clean()  # Should not raise.
            else:
                self.assertRaises(ValidationError, clean)


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


class SetPasswordFormTests(TestCaseBase):
    """SetPasswordForm tests."""

    def test_common_password(self):
        form = SetPasswordForm(
            None, data={"new_password1": "password", "new_password2": "password"}
        )
        assert not form.is_valid()


class PasswordChangeFormFormTests(TestCaseBase):
    """PasswordChangeForm tests."""

    def test_common_password(self):
        u = UserFactory()
        form = SetPasswordForm(
            u,
            data={
                "new_password1": "password",
                "new_password2": "password",
                "old_password": "testpass",
            },
        )
        assert not form.is_valid()


class ForgotUsernameFormTests(TestCaseBase):
    """ForgotUsernameForm tests."""

    def test_email_doesnt_exist(self):
        """If no account with email exists, form isn't valid."""
        form = ForgotUsernameForm({"email": "a@b.com"})
        assert not form.is_valid()

    def test_valid_email(self):
        """"If an account with email exists, form is valid."""
        u = UserFactory(email="a@b.com", is_active=True)
        form = ForgotUsernameForm({"email": u.email})
        assert form.is_valid()


class Testusername_allowed(TestCase):
    def test_good_names(self):
        data = [
            ("ana", True),
            ("rlr", True),
            ("anal", False),
        ]

        for name, expected in data:
            eq_(username_allowed(name), expected)
