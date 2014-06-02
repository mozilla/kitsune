# -*- coding: utf-8 -*-
from nose.tools import eq_

from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.users.models import UserMappingType
from kitsune.users.tests import profile, user


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

        self.refresh()

        eq_(UserMappingType.search().count(), 1)
        data = UserMappingType.search().values_dict()[0]
        eq_(data['username'], p.user.username)
        eq_(data['display_name'], p.name)

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
