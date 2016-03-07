import json
from datetime import datetime, timedelta
from random import random

import mock
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from nose.tools import eq_
from rest_framework.test import APIClient

from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.questions.tests import (QuestionFactory, AnswerFactory,
                                     AnswerVoteFactory, SolutionAnswerFactory)
from kitsune.users import api
from kitsune.users.models import Profile, Setting
from kitsune.users.tests import ProfileFactory, SettingFactory, UserFactory


class UsernamesTests(TestCase):
    """Test the usernames API method."""
    url = reverse('users.api.usernames', locale='en-US')

    def setUp(self):
        self.u = UserFactory(username='testUser')
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
        serializer.is_valid(raise_exception=True)
        serializer.save()
        eq_(User.objects.count(), number_users + 1)
        eq_(Profile.objects.count(), 1)

    def test_password(self):
        serializer = api.ProfileSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        assert obj.user.password != 'testpass'
        assert obj.user.check_password('testpass')

    def test_automatic_display_name(self):
        del self.data['display_name']
        serializer = api.ProfileSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        eq_(obj.name, 'bobb')

    def test_no_duplicate_emails(self):
        UserFactory(email=self.data['email'])
        serializer = api.ProfileSerializer(data=self.data)
        assert not serializer.is_valid()
        eq_(serializer.errors, {
            'email': ['A user with that email address already exists.'],
        })

    def test_users_with_emails_are_inactive(self):
        serializer = api.ProfileSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        eq_(obj.user.is_active, False)

    def test_users_with_emails_get_confirmation_email(self):
        serializer = api.ProfileSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        eq_(len(mail.outbox), 1)
        eq_(mail.outbox[0].subject, 'Please confirm your email address')

    def test_cant_update_username(self):
        p = ProfileFactory(user__username='notbob')

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

    def test_helpfulness(self):
        u = UserFactory()
        p = u.profile
        a1 = AnswerFactory(creator=u)
        a2 = AnswerFactory(creator=u)

        AnswerVoteFactory(answer=a1, helpful=True)
        AnswerVoteFactory(answer=a2, helpful=True)
        AnswerVoteFactory(answer=a2, helpful=True)
        # Some red herrings.
        AnswerVoteFactory(creator=u)
        AnswerVoteFactory(answer=a1, helpful=False)

        serializer = api.ProfileSerializer(instance=p)
        eq_(serializer.data['helpfulness'], 3)

    def test_counts(self):
        u = UserFactory()
        p = u.profile
        q = QuestionFactory(creator=u)
        AnswerFactory(creator=u)
        q.solution = AnswerFactory(question=q, creator=u)
        q.save()

        serializer = api.ProfileSerializer(instance=p)
        eq_(serializer.data['question_count'], 1)
        eq_(serializer.data['answer_count'], 2)
        eq_(serializer.data['solution_count'], 1)

    def test_last_answer_date(self):
        p = ProfileFactory()
        u = p.user
        AnswerFactory(creator=u)

        serializer = api.ProfileSerializer(instance=p)
        eq_(serializer.data['last_answer_date'], u.answers.last().created)


class TestUserView(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_usernames_with_periods(self):
        u = UserFactory(username='something.something')
        url = reverse('user-detail', args=[u.username])
        res = self.client.get(url)
        eq_(res.status_code, 200)
        eq_(res.data['username'], u.username)

    def test_only_self_edits(self):
        p1 = ProfileFactory()
        p2 = ProfileFactory()
        self.client.force_authenticate(user=p2.user)
        url = reverse('user-detail', args=[p1.user.username])
        res = self.client.patch(url, {})
        # u2 should not have permission to edit u1's user.
        eq_(res.status_code, 403)

    def test_cant_delete(self):
        p = ProfileFactory()
        self.client.force_authenticate(user=p.user)
        url = reverse('user-detail', args=[p.user.username])
        res = self.client.delete(url)
        eq_(res.status_code, 405)

    def test_generator_on_stage(self):
        # There is at least one user made during tests.
        old_user_count = User.objects.count()
        res = self.client.post(reverse('user-generate'))
        eq_(res.status_code, 200)
        eq_(User.objects.count(), old_user_count + 1)
        new_user = User.objects.order_by('-id')[0]
        eq_(res.data['user']['username'], new_user.username)
        assert 'password' in res.data
        assert 'token' in res.data

    def test_generated_users_tagged(self):
        res = self.client.post(reverse('user-generate'))
        eq_(res.status_code, 200)
        profile = Profile.objects.get()
        eq_(profile.settings.get(name='autogenerated').value, 'true')

    def test_weekly_solutions(self):
        eight_days_ago = datetime.now() - timedelta(days=8)
        # First one is a solution, but it is too old.
        # second answer is not a solution.
        SolutionAnswerFactory(created=eight_days_ago)
        AnswerFactory()
        res = self.client.get(reverse('user-weekly-solutions'))
        eq_(res.status_code, 200)
        eq_(len(res.data), 0)

        # Check that the data about the contributors is showing currectly
        user_info_list = []  # Info list with username and their number of solutions
        top_answer_number = 15
        for i in range(12):
            user = UserFactory()
            SolutionAnswerFactory.create_batch(top_answer_number, creator=user)
            user_info_list.append((user.username, top_answer_number))
            top_answer_number -= 1

        res = self.client.get(reverse('user-weekly-solutions'))
        eq_(res.status_code, 200)
        # Check only 10 users information is present there
        eq_(len(res.data), 10)
        # Create a list of the data with only the ``username`` and ``weekly_solutions``
        data_list = [(data['username'], data['weekly_solutions']) for data in res.data]

        # Check only top 10 contributor information is in the API
        top_ten = user_info_list[:10]
        eq_(sorted(top_ten), sorted(data_list))

    def test_email_visible_when_signed_in(self):
        p = ProfileFactory()
        url = reverse('user-detail', args=[p.user.username])
        self.client.force_authenticate(user=p.user)
        res = self.client.get(url)
        eq_(res.data['email'], p.user.email)

    def test_email_not_visible_when_signed_out(self):
        p = ProfileFactory()
        url = reverse('user-detail', args=[p.user.username])
        res = self.client.get(url)
        assert 'email' not in res.data

    def test_set_setting_add(self):
        p = ProfileFactory()
        self.client.force_authenticate(user=p.user)
        url = reverse('user-set-setting', args=[p.user.username])
        res = self.client.post(url, {'name': 'foo', 'value': 'bar'})
        eq_(res.status_code, 200)
        eq_(p.settings.get(name='foo').value, 'bar')

    def test_set_setting_update(self):
        p = ProfileFactory()
        self.client.force_authenticate(user=p.user)
        s = SettingFactory(user=p.user, name='favorite_fruit', value='apple')
        url = reverse('user-set-setting', args=[p.user.username])
        res = self.client.post(url, {'name': 'favorite_fruit', 'value': 'banana'})
        eq_(res.status_code, 200)
        eq_(res.data['value'], 'banana')
        s = Setting.objects.get(id=s.id)
        eq_(s.value, 'banana')

    def test_delete_setting_exists_with_post(self):
        p = ProfileFactory()
        self.client.force_authenticate(user=p.user)
        s = SettingFactory(user=p.user)
        url = reverse('user-delete-setting', args=[p.user.username])
        res = self.client.post(url, {'name': s.name})
        eq_(res.status_code, 204)
        eq_(p.settings.filter(name=s.name).count(), 0)

    def test_delete_setting_exists_with_delete(self):
        p = ProfileFactory()
        self.client.force_authenticate(user=p.user)
        s = SettingFactory(user=p.user)
        url = reverse('user-delete-setting', args=[p.user.username])
        res = self.client.delete(url, {'name': s.name})
        eq_(res.status_code, 204)
        eq_(p.settings.filter(name=s.name).count(), 0)

    def test_delete_setting_404(self):
        p = ProfileFactory()
        self.client.force_authenticate(user=p.user)
        url = reverse('user-delete-setting', args=[p.user.username])
        res = self.client.post(url, {'name': 'nonexistant'})
        eq_(res.status_code, 404)

    def test_settings_visible_when_signed_in(self):
        p = ProfileFactory()
        p.settings.create(name='foo', value='bar')
        url = reverse('user-detail', args=[p.user.username])
        self.client.force_authenticate(user=p.user)
        res = self.client.get(url)
        eq_(res.data['settings'], [{'name': 'foo', 'value': 'bar'}])

    def test_settings_not_visible_when_signed_out(self):
        p = ProfileFactory()
        p.settings.create(name='foo', value='bar')
        url = reverse('user-detail', args=[p.user.username])
        res = self.client.get(url)
        assert 'settings' not in res.data

    def test_is_active(self):
        p = ProfileFactory()
        url = reverse('user-detail', args=[p.user.username])
        res = self.client.get(url)
        assert 'is_active' in res.data

    @mock.patch.object(Site.objects, 'get_current')
    def test_request_password_reset(self, get_current):
        get_current.return_value.domain = 'testserver'
        p = ProfileFactory()
        url = reverse('user-request-password-reset', args=[p.user.username])
        res = self.client.get(url)
        eq_(res.status_code, 204)
        eq_(1, len(mail.outbox))

    def test_avatar_size(self):
        p = ProfileFactory()
        url = reverse('user-detail', args=[p.user.username])

        res = self.client.get(url)
        assert '?s=48' in res.data['avatar']

        res = self.client.get(url, {'avatar_size': 128})
        assert '?s=128' in res.data['avatar']

    def test_create_user(self):
        # There is at least one user in existence due to migrations
        number_users = User.objects.count()

        username = 'kris-{}'.format(random())
        url = reverse('user-list')
        res = self.client.post(url, {
            'username': username,
            'password': 'testpass',
            'email': 'kris@example.com'
        })

        eq_(res.status_code, 201)
        eq_(User.objects.count(), number_users + 1)
        u = User.objects.order_by('-id')[0]
        eq_(u.username, username)
        eq_(u.email, 'kris@example.com')
        eq_(u.is_active, False)

    def test_invalid_email(self):
        username = 'sarah-{}'.format(random())
        url = reverse('user-list')
        res = self.client.post(url, {
            'username': username,
            'password': 'testpass',
            'email': 'sarah',  # invalid
        })
        eq_(res.status_code, 400)
        eq_(res.data, {'email': [u'Enter a valid email address.']})

    def test_invalid_username(self):
        url = reverse('user-list')
        res = self.client.post(url, {
            'username': '&',  # invalid
            'password': 'testpass',
            'email': 'lucy@example.com',
        })
        eq_(res.status_code, 400)
        eq_(res.data, {'username': [u'Usernames may only be letters, numbers, "." and "-".']})

    def test_too_short_username(self):
        url = reverse('user-list')
        res = self.client.post(url, {
            'username': 'a',  # too short
            'password': 'testpass',
            'email': 'lucy@example.com',
        })
        eq_(res.status_code, 400)
        eq_(res.data, {'username': [u'Usernames may only be letters, numbers, "." and "-".']})

    def test_too_long_username(self):
        url = reverse('user-list')
        res = self.client.post(url, {
            'username': 'a' * 100,  # too long
            'password': 'testpass',
            'email': 'lucy@example.com',
        })
        eq_(res.status_code, 400)
        eq_(res.data, {'username': [u'Usernames may only be letters, numbers, "." and "-".']})

    def test_change_user_with_patch(self):
        user = UserFactory()
        new_display_name = user.profile.name.upper()
        data = {
            'display_name': new_display_name,
            'locale': 'en-US',
            'username': user.username,
            'password': 'testpass',
        }
        url = reverse('user-detail', args=[user.username])
        self.client.force_authenticate(user=user)
        res = self.client.patch(url, data)
        eq_(res.status_code, 200)

        user = User.objects.get(id=user.id)
        eq_(user.profile.display_name, new_display_name)
