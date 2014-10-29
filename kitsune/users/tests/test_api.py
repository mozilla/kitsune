import json

import mock
from django.contrib.auth.models import User
from django.core import mail
from nose.tools import eq_, ok_
from rest_framework.test import APIClient

from kitsune.sumo.helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users import api
from kitsune.users.models import Profile
from kitsune.users.tests import user, profile


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


class TestUserSerializer(TestCase):

    def setUp(self):
        self.request = mock.Mock()
        self.data = {
            'username': 'bobb',
            'display_name': 'Bobbert the Seventh',
            'password': 'testpass',
            'email': 'bobb@example.com',
        }

    def test_user_created(self):
        # There is at least one user in existence due to migrations
        number_users = User.objects.count()
        serializer = api.ProfileSerializer(data=self.data)
        ok_(serializer.is_valid())
        serializer.save()
        eq_(User.objects.count(), number_users + 1)
        eq_(Profile.objects.count(), 1)

    def test_password(self):
        serializer = api.ProfileSerializer(data=self.data)
        ok_(serializer.is_valid())
        serializer.save()
        assert serializer.object.user.password != 'testpass'
        ok_(serializer.object.user.check_password('testpass'))

    def test_automatic_display_name(self):
        del self.data['display_name']
        serializer = api.ProfileSerializer(data=self.data)
        ok_(serializer.is_valid())
        eq_(serializer.object.name, 'bobb')

    def test_no_duplicate_emails(self):
        user(email=self.data['email'], save=True)
        serializer = api.ProfileSerializer(data=self.data)
        eq_(serializer.errors, {
            'email': ['A user with that email address already exists.'],
        })
        ok_(not serializer.is_valid())

    def test_users_without_emails_are_active(self):
        del self.data['email']
        serializer = api.ProfileSerializer(data=self.data)
        ok_(serializer.is_valid())
        serializer.save()
        eq_(serializer.object.user.is_active, True)

    def test_users_with_emails_are_inactive(self):
        serializer = api.ProfileSerializer(data=self.data)
        ok_(serializer.is_valid())
        serializer.save()
        eq_(serializer.object.user.is_active, False)

    def test_users_with_emails_get_confirmation_email(self):
        serializer = api.ProfileSerializer(data=self.data)
        ok_(serializer.is_valid())
        serializer.save()
        eq_(len(mail.outbox), 1)
        eq_(mail.outbox[0].subject, 'Please confirm your email address')

    def test_cant_update_username(self):
        p = profile()
        p.user.username = 'notbobb'
        p.user.save()

        serializer = api.ProfileSerializer(data=self.data, instance=p)
        eq_(serializer.is_valid(), False)
        eq_(serializer.errors, {
            'username': [u"Can't change this field."],
        })

    def test_username_bad_chars(self):
        # New users shouldn't be able to have '@' in their username.
        self.data['username'] = 'bobb@example.com'
        serializer = api.ProfileSerializer(data=self.data)
        eq_(serializer.is_valid(), False)
        eq_(serializer.errors, {'username':
            [u'Usernames may only be letters, numbers, "." and "-".']})

    def test_username_too_long(self):
        # Max length is 30
        self.data['username'] = 'B' * 31
        serializer = api.ProfileSerializer(data=self.data)
        eq_(serializer.is_valid(), False)
        eq_(serializer.errors, {'username':
            [u'Usernames may only be letters, numbers, "." and "-".']})

    def test_username_too_short(self):
        # Min length is 4 chars.
        self.data['username'] = 'bob'
        serializer = api.ProfileSerializer(data=self.data)
        eq_(serializer.is_valid(), False)
        eq_(serializer.errors, {'username':
            [u'Usernames may only be letters, numbers, "." and "-".']})


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


class TestUserView(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_only_self_edits(self):
        p1 = profile()
        p2 = profile()
        self.client.force_authenticate(user=p2.user)
        url = reverse('user-detail', args=[p1.user.username])
        res = self.client.patch(url, {})
        # u2 should not have permission to edit u1's user.
        eq_(res.status_code, 403)

    def test_cant_delete(self):
        p = profile()
        self.client.force_authenticate(user=p.user)
        url = reverse('user-detail', args=[p.user.username])
        res = self.client.delete(url)
        eq_(res.status_code, 405)
