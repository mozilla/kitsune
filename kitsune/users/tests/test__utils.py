from django.contrib.auth.models import User

from nose.tools import eq_

from kitsune.sumo.tests import TestCase
from kitsune.users.utils import suggest_username

class UtilsTestCase(TestCase):
    def test_suggest_username(self):
        eq_('someuser', suggest_username('someuser@test.com'))

        User.objects.create(username='someuser')
        suggested = suggest_username('someuser@test.com')

        eq_('someuser1', suggested)

        User.objects.create(username='someuser4')
        suggested = suggest_username('someuser@test.com')
        eq_('someuser1', suggested)

        User.objects.create(username='ricky')
        User.objects.create(username='Ricky1')
        User.objects.create(username='ricky33')
        suggested = suggest_username('rIcky@test.com')
        eq_('rIcky2', suggested)
