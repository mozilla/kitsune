from datetime import timedelta
import logging

from django.contrib.auth.models import User
from django.contrib.sites.models import Site

import mock
from nose.tools import eq_

from sumo.tests import TestCase
from users.models import RegistrationProfile, Setting
from users.forms import SettingsForm
from users.tests import profile


log = logging.getLogger('k.users')


class ProfileTests(TestCase):
    fixtures = ['users.json']

    def test_user_get_profile(self):
        """user.get_profile() returns what you'd expect."""
        user = User.objects.all()[0]
        p = profile(user=user)

        eq_(p, user.get_profile())


class RegistrationProfileTests(TestCase):
    @mock.patch.object(Site.objects, 'get_current')
    def test_create_inactive_user_locale(self, get_current):
        get_current.return_value.domain = 'testserver'

        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com', locale='fr')
        eq_('fr', user.profile.locale)

    @mock.patch.object(log, 'warning')
    def test_activation_key_invalid(self, warning):
        key = 'foobar'
        RegistrationProfile.objects.activate_user(key)
        assert warning.called
        eq_('User activation failure (invalid key): {k}'.format(k=key),
            warning.call_args[0][0])

    @mock.patch.object(log, 'warning')
    def test_activation_key_doesnt_exist(self, warning):
        key = '1234567890123456789012345678901234567890'
        RegistrationProfile.objects.activate_user(key)
        assert warning.called
        eq_('User activation failure (key not found): {k}'.format(k=key),
            warning.call_args[0][0])

    @mock.patch.object(Site.objects, 'get_current')
    @mock.patch.object(log, 'warning')
    def test_activation_key_expired(self, warning, get_current):
        get_current.return_value.domain = 'testserver'
        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')
        profile = RegistrationProfile.objects.get(user=user)
        user.date_joined = user.date_joined - timedelta(days=1000)
        user.save()
        RegistrationProfile.objects.activate_user(profile.activation_key)
        assert warning.called
        eq_('User activation failure (key expired): {k}'.format(
            k=profile.activation_key), warning.call_args[0][0])


class UserSettingsTests(TestCase):
    fixtures = ['users.json']

    def test_non_existant_setting(self):
        user = User.objects.all()[0]
        form = SettingsForm()
        bad_setting = 'doesnt_exist'
        assert bad_setting not in form.fields.keys()
        with self.assertRaises(KeyError):
            Setting.get_for_user(user, bad_setting)

    def test_default_values(self):
        eq_(0, Setting.objects.count())
        user = User.objects.get(username='timw')
        keys = SettingsForm.base_fields.keys()
        for setting in keys:
            field = SettingsForm.base_fields[setting]
            eq_(field.initial, Setting.get_for_user(user, setting))
