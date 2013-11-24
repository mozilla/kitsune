from datetime import timedelta
import logging

from django.contrib.auth.models import User
from django.contrib.sites.models import Site

import mock
from nose.tools import eq_

from kitsune.sumo.tests import TestCase
from kitsune.users.models import RegistrationProfile, Setting, Deactivation
from kitsune.users.forms import SettingsForm
from kitsune.users.tests import user, profile


log = logging.getLogger('k.users')


class ProfileTests(TestCase):

    def test_user_get_profile(self):
        """user.get_profile() returns what you'd expect."""
        u = user(save=True)
        p = profile(user=u)

        eq_(p, u.get_profile())


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

    def setUp(self):
        self.u = user(save=True)

    def test_non_existant_setting(self):
        form = SettingsForm()
        bad_setting = 'doesnt_exist'
        assert bad_setting not in form.fields.keys()
        with self.assertRaises(KeyError):
            Setting.get_for_user(self.u, bad_setting)

    def test_default_values(self):
        eq_(0, Setting.objects.count())
        keys = SettingsForm.base_fields.keys()
        for setting in keys:
            field = SettingsForm.base_fields[setting]
            eq_(field.initial, Setting.get_for_user(self.u, setting))

class DeactivationsTests(TestCase):

    def setUp(self):
        self.user = user(save=True)
        self.moderator = user(save=True)

    def test_deactivate_user(self):
        assert self.user.is_active
        d = Deactivation(user=self.user, moderator=self.moderator)
        d.save()
        assert not self.user.is_active
