import json

from django.test import LiveServerTestCase
from django.test.client import Client

from nose.tools import eq_

from kitsune.customercare.models import TwitterAccount
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import add_permission, user


class BanUser(TestCase):

    def setUp(self):
        # Set up some banned users
        self.banned_usernames = ['deanj', 'r1cky', 'mythmon']
        for username in self.banned_usernames:
            TwitterAccount.objects.create(username=username, banned=True)

        # Now a few normal users
        self.normal_usernames = ['willkg', 'marcell', 'ian']
        for username in self.normal_usernames:
            TwitterAccount.objects.create(username=username, banned=False)

        # Create a user with permissions to ban
        u = user(save=True)
        add_permission(u, TwitterAccount, 'ban_account')
        self.client.login(username=u.username, password='testpass')

    def test_account_in_banned_list(self):
        users = self.client.get(reverse('customercare.api.banned')).data
        usernames = [user['username'] for user in users]
        eq_(sorted(usernames), sorted(self.banned_usernames))

    def test_account_not_in_banned_list(self):
        users = self.client.get(reverse('customercare.api.banned')).data
        usernames = [user['username'] for user in users]
        for username in self.normal_usernames:
            assert username not in usernames

    def test_ban_account(self):
        data = {'username': 'rehan'}
        self.client.post(reverse('customercare.api.ban'),
                         data=json.dumps(data),
                         content_type='application/json')
        user = TwitterAccount.objects.get(username=data['username'])
        eq_(user.banned, True)

    def test_single_unban_account(self):
        data = {'usernames': ['deanj']}
        self.client.post(reverse('customercare.api.unban'),
                         data=json.dumps(data),
                         content_type='application/json')

        num_banned = TwitterAccount.objects.filter(banned=True).count()
        eq_(num_banned, 2)

        user = (TwitterAccount.objects
                .filter(username__in=data['usernames'], banned=False).first())
        eq_(user.banned, False)

    def test_multiple_unban_account(self):
        data = {'usernames': ['r1cky', 'mythmon']}
        self.client.post(reverse('customercare.api.unban'),
                         data=json.dumps(data),
                         content_type='application/json')

        num_banned = TwitterAccount.objects.filter(banned=True).count()
        eq_(num_banned, 1)

        users = (TwitterAccount.objects
                 .filter(username__in=data['usernames']).all())
        for u in users:
            eq_(u.banned, False)
