from django.contrib.auth.models import User

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
    def test_create_inactive_user_locale(self):
        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com', locale='fr')
        eq_('fr', user.profile.locale)
