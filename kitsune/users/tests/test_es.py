# -*- coding: utf-8 -*-
from datetime import datetime

from nose.tools import eq_

from kitsune.customercare.tests import reply
from kitsune.questions.tests import answer
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.users.models import UserMappingType
from kitsune.users.tests import profile, user
from kitsune.wiki.tests import revision


class UserSearchTests(ElasticTestCase):
    def test_add_and_delete(self):
        """Adding a user with a profile should add it to the index.

        Deleting should delete it.
        """
        p = profile()
        self.refresh()
        eq_(UserMappingType.search().count(), 1)

        p.user.delete()
        self.refresh()
        eq_(UserMappingType.search().count(), 0)

    def test_data_in_index(self):
        """Verify the data we are indexing."""
        u = user(username='r1cky', email='r@r.com', save=True)
        p = profile(user=u, name=u'Rick Róss')
        r1 = reply(user=u, twitter_username='r1cardo', save=True)
        r2 = reply(user=u, twitter_username='r1cky', save=True)

        self.refresh()

        eq_(UserMappingType.search().count(), 1)
        data = UserMappingType.search().values_dict()[0]
        eq_(data['username'], p.user.username)
        eq_(data['display_name'], p.name)
        assert r1.twitter_username in data['twitter_usernames']
        assert r2.twitter_username in data['twitter_usernames']

        u = user(username='willkg', email='w@w.com', save=True)
        p = profile(user=u, name=u'Will Cage')
        self.refresh()
        eq_(UserMappingType.search().count(), 2)

    def test_suggest_completions(self):
        u1 = user(username='r1cky', save=True)
        profile(user=u1, name=u'Rick Róss')
        u2 = user(username='Willkg', save=True)
        profile(user=u2, name=u'Will Cage')

        self.refresh()
        eq_(UserMappingType.search().count(), 2)

        results = UserMappingType.suggest_completions('wi')
        eq_(1, len(results))
        eq_('Will Cage (Willkg)', results[0]['text'])
        eq_(u2.id, results[0]['payload']['user_id'])

        results = UserMappingType.suggest_completions('R1')
        eq_(1, len(results))
        eq_(u'Rick Róss (r1cky)', results[0]['text'])
        eq_(u1.id, results[0]['payload']['user_id'])

        # Add another Ri....
        u3 = user(username='richard', save=True)
        profile(user=u3, name=u'Richard Smith')

        self.refresh()
        eq_(UserMappingType.search().count(), 3)

        results = UserMappingType.suggest_completions('ri')
        eq_(2, len(results))
        texts = [r['text'] for r in results]
        assert u'Rick Róss (r1cky)' in texts
        assert u'Richard Smith (richard)' in texts

        results = UserMappingType.suggest_completions(u'Rick Ró')
        eq_(1, len(results))
        texts = [r['text'] for r in results]
        eq_(u'Rick Róss (r1cky)', results[0]['text'])

    def test_suggest_completions_numbers(self):
        u1 = user(username='1337mike', save=True)
        profile(user=u1, name=u'Elite Mike')
        u2 = user(username='crazypants', save=True)
        profile(user=u2, name=u'Crazy Pants')

        self.refresh()
        eq_(UserMappingType.search().count(), 2)

        results = UserMappingType.suggest_completions('13')
        eq_(1, len(results))
        eq_('Elite Mike (1337mike)', results[0]['text'])
        eq_(u1.id, results[0]['payload']['user_id'])

    def test_query_username_with_numbers(self):
        u1 = user(username='1337miKE', save=True)
        p = profile(user=u1, name=u'Elite Mike')
        u2 = user(username='mike', save=True)
        profile(user=u2, name=u'NotElite Mike')

        self.refresh()

        eq_(UserMappingType.search().query(
            iusername__match='1337mike').count(), 1)
        data = UserMappingType.search().query(
            iusername__match='1337mike').values_dict()[0]
        eq_(data['username'], p.user.username)
        eq_(data['display_name'], p.name)

    def test_query_display_name_with_whitespace(self):
        u1 = user(username='1337miKE', save=True)
        p = profile(user=u1, name=u'Elite Mike')
        u2 = user(username='mike', save=True)
        profile(user=u2, name=u'NotElite Mike')

        self.refresh()

        eq_(UserMappingType.search().count(), 2)
        eq_(UserMappingType.search().query(
            idisplay_name__match_whitespace='elite').count(), 1)

    def test_query_twitter_usernames(self):
        u1 = user(username='1337miKE', save=True)
        p = profile(user=u1, name=u'Elite Mike')
        u2 = user(username='mike', save=True)
        profile(user=u2, name=u'NotElite Mike')
        r1 = reply(user=u1, twitter_username='l33tmIkE', save=True)
        r2 = reply(user=u2, twitter_username='mikey', save=True)

        self.refresh()

        eq_(UserMappingType.search().query(
            itwitter_usernames__match='l33tmike').count(), 1)
        data = UserMappingType.search().query(
            itwitter_usernames__match='l33tmike').values_dict()[0]
        eq_(data['username'], p.user.username)
        eq_(data['display_name'], p.name)
        assert r1.twitter_username in data['twitter_usernames']

    def test_last_contribution_date(self):
        """Verify the last_contribution_date field works properly."""
        u = user(username='satdav', save=True)
        p = profile(user=u)

        self.refresh()

        data = UserMappingType.search().query(
            username__match='satdav').values_dict()[0]
        assert not data['last_contribution_date']

        # Add a AoA reply. It should be the last contribution.
        d = datetime(2014, 1, 1)
        reply(user=u, created=d, save=True)

        self.refresh()

        data = UserMappingType.search().query(
            username__match='satdav').values_dict()[0]
        eq_(data['last_contribution_date'], d)

        # Add a Support Forum answer. It should be the last contribution.
        d = datetime(2014, 1, 2)
        answer(creator=u, created=d, save=True)

        self.refresh()

        data = UserMappingType.search().query(
            username__match='satdav').values_dict()[0]
        eq_(data['last_contribution_date'], d)

        # Add a Revision edit. It should be the last contribution.
        d = datetime(2014, 1, 3)
        revision(creator=u, created=d, save=True)

        self.refresh()

        data = UserMappingType.search().query(
            username__match='satdav').values_dict()[0]
        eq_(data['last_contribution_date'], d)

        # Add a Revision review. It should be the last contribution.
        d = datetime(2014, 1, 4)
        revision(reviewer=u, reviewed=d, save=True)

        self.refresh()

        data = UserMappingType.search().query(
            username__match='satdav').values_dict()[0]
        eq_(data['last_contribution_date'], d)
