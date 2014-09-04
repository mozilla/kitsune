import json

from nose.tools import eq_

from kitsune.customercare.models import TwitterAccount
from kitsune.customercare.tests import twitter_account
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import add_permission, user


class BanUser(TestCase):

    def setUp(self):
        # Set up some banned users
        self.banned_usernames = ['deanj', 'r1cky', 'mythmon']
        for username in self.banned_usernames:
            twitter_account(username=username, banned=True, save=True)

        # Now a few normal users
        self.normal_usernames = ['willkg', 'marcell', 'ian']
        for username in self.normal_usernames:
            twitter_account(username=username, banned=False, save=True)

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
        import q
        q(users)
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
        data = {'usernames': self.banned_usernames[:1]}
        self.client.post(reverse('customercare.api.unban'),
                         data=json.dumps(data),
                         content_type='application/json')

        num_banned = TwitterAccount.objects.filter(banned=True).count()
        eq_(num_banned, 2)

        user = (TwitterAccount.objects
                .filter(username__in=data['usernames'], banned=False)
                .first())
        eq_(user.banned, False)

    def test_multiple_unban_account(self):
        data = {'usernames': self.banned_usernames[1:]}
        self.client.post(reverse('customercare.api.unban'),
                         data=json.dumps(data),
                         content_type='application/json')

        num_banned = TwitterAccount.objects.filter(banned=True).count()
        eq_(num_banned, 1)

        users = (TwitterAccount.objects
                 .filter(username__in=data['usernames']).all())
        for u in users:
            eq_(u.banned, False)


class IgnoreUser(TestCase):

    def setUp(self):
        # Set up some ignored users
        self.ignored_usernames = ['deanj', 'r1cky', 'mythmon']
        for username in self.ignored_usernames:
            twitter_account(username=username, ignored=True, save=True)

        # Now a few normal users
        self.normal_usernames = ['willkg', 'marcell', 'ian']
        for username in self.normal_usernames:
            twitter_account(username=username, ignored=False, save=True)

        # Create a user with permissions to ignore
        u = user(save=True)
        add_permission(u, TwitterAccount, 'ignore_account')
        self.client.login(username=u.username, password='testpass')

    def test_account_in_ignored_list(self):
        users = self.client.get(reverse('customercare.api.ignored')).data
        usernames = [user['username'] for user in users]
        eq_(sorted(usernames), sorted(self.ignored_usernames))

    def test_account_not_in_ignored_list(self):
        users = self.client.get(reverse('customercare.api.ignored')).data
        usernames = [user['username'] for user in users]
        for username in self.normal_usernames:
            assert username not in usernames

    def test_ignore_account(self):
        data = {'username': 'rehan'}
        res = self.client.post(reverse('customercare.api.ignore'),
                               data=json.dumps(data),
                               content_type='application/json')
        eq_(res.status_code, 200)
        user = TwitterAccount.objects.get(username=data['username'])
        eq_(user.ignored, True)

    def test_single_unignore_account(self):
        data = {'usernames': self.ignored_usernames[:1]}
        self.client.post(reverse('customercare.api.unignore'),
                         data=json.dumps(data),
                         content_type='application/json')

        num_ignored = TwitterAccount.objects.filter(ignored=True).count()
        eq_(num_ignored, 2)

        user = (TwitterAccount.objects
                .filter(username__in=data['usernames'], ignored=False)
                .first())
        eq_(user.ignored, False)

    def test_multiple_unignore_account(self):
        data = {'usernames': self.ignored_usernames[1:]}
        self.client.post(reverse('customercare.api.unignore'),
                         data=json.dumps(data),
                         content_type='application/json')

        num_ignored = TwitterAccount.objects.filter(ignored=True).count()
        eq_(num_ignored, 1)

        users = (TwitterAccount.objects
                 .filter(username__in=data['usernames']).all())
        for u in users:
            eq_(u.ignored, False)
