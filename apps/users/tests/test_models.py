from django.contrib.auth.models import User
from django.contrib.sites.models import Site

import mock
from nose.tools import eq_

from sumo.tests import TestCase
from users.models import RegistrationProfile
from users.tests import profile


class ProfileTests(TestCase):
    fixtures = ['users.json']

    def test_user_get_profile(self):
        """user.get_profile() returns what you'd expect."""
        user = User.objects.all()[0]
        p = profile(user)

        eq_(p, user.get_profile())


class RegistrationProfileTests(TestCase):
    @mock.patch.object(Site.objects, 'get_current')
    def test_create_inactive_user_locale(self, get_current):
        get_current.return_value.domain = 'testserver'

        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com', locale='fr')
        eq_('fr', user.profile.locale)
