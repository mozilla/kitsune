import json

import mock
from django.contrib.auth.models import User
from django.core import mail
from nose.tools import eq_, ok_

from kitsune.sumo.helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users import api
from kitsune.users.models import Profile
from kitsune.users.tests import user


class UsernamesTests(TestCase):
    """Test the usernames API method."""
    url = reverse('users.api.usernames', locale='en-US')

    def setUp(self):
        self.u = user(username='testUser', save=True)
        self.client.login(username=self.u.username, password='testpass')

    def tearDown(self):
        self.client.logout()

    def test_no_query(self):
        res = self.client.get(self.url)
        eq_(200, res.status_code)
        eq_('[]', res.content)

    def test_query_old(self):
        res = self.client.get(urlparams(self.url, term='a'))
        eq_(200, res.status_code)
        data = json.loads(res.content)
        eq_(0, len(data))

    def test_query_current(self):
        res = self.client.get(urlparams(self.url, term=self.u.username[0]))
        eq_(200, res.status_code)
        data = json.loads(res.content)
        eq_(1, len(data))

    def test_post(self):
        res = self.client.post(self.url)
        eq_(405, res.status_code)

    def test_logged_out(self):
        self.client.logout()
        res = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(403, res.status_code)


class TestQuestionSerializer(TestCase):

    def setUp(self):
        self.request = mock.Mock()
        self.data = {
            'username': 'bob',
            'display_name': 'Bobert the Seventh',
            'password': 'testpass',
            'email': 'bob@example.com',
        }

    def test_user_created(self):
        # There is at least one user in existence due to migrations
        number_users = User.objects.count()
        serializer = api.ProfileShortSerializer(data=self.data)
        ok_(serializer.is_valid())
        serializer.save()
        eq_(User.objects.count(), number_users + 1)
        eq_(Profile.objects.count(), 1)

    def test_password(self):
        serializer = api.ProfileShortSerializer(data=self.data)
        ok_(serializer.is_valid())
        serializer.save()
        assert serializer.object.user.password != 'testpass'
        ok_(serializer.object.user.check_password('testpass'))

    def test_automatic_display_name(self):
        del self.data['display_name']
        serializer = api.ProfileShortSerializer(data=self.data)
        ok_(serializer.is_valid())
        eq_(serializer.object.name, 'bob')

    def test_no_duplicate_emails(self):
        user(email=self.data['email'], save=True)
        serializer = api.ProfileShortSerializer(data=self.data)
        eq_(serializer.errors, {
            'email': ['A user with that email address already exists.'],
        })
        ok_(not serializer.is_valid())

    def test_users_without_emails_are_active(self):
        del self.data['email']
        serializer = api.ProfileShortSerializer(data=self.data)
        ok_(serializer.is_valid())
        serializer.save()
        eq_(serializer.object.user.is_active, True)

    def test_users_with_emails_are_inactive(self):
        serializer = api.ProfileShortSerializer(data=self.data)
        ok_(serializer.is_valid())
        serializer.save()
        eq_(serializer.object.user.is_active, False)

    def test_users_with_emails_get_confirmation_email(self):
        serializer = api.ProfileShortSerializer(data=self.data)
        ok_(serializer.is_valid())
        serializer.save()
        eq_(len(mail.outbox), 1)
        eq_(mail.outbox[0].subject, 'Please confirm your email address')


class TestGetToken(TestCase):

    def setUp(self):
        self.url = reverse('users.get_token')
        self.user = user(password='testpass', save=True)
        self.data = {
            'username': self.user.username,
            'password': 'testpass',
        }

    def test_it_works(self):
        res = self.client.post(self.url, data=self.data)
        eq_(res.status_code, 200)
        eq_(res.data.keys(), ['token'])

    def test_it_has_cors(self):
        res = self.client.post(self.url, data=self.data)
        eq_(res.status_code, 200)
        ok_(res.has_header('Access-Control-Allow-Origin'))
