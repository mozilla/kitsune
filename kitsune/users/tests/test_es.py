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
        u1 = user(username='r1cky', email='r@r.com', save=True)
        profile(user=u1, name=u'Rick Róss')
        u2 = user(username='willkg', email='w@w.com', save=True)
        profile(user=u2, name=u'Will Cage')

        self.refresh()
        eq_(UserMappingType.search().count(), 2)

        results = UserMappingType.suggest_completions('wi')
        eq_(1, len(results))
        eq_('Will Cage (willkg)', results[0]['text'])
        eq_(u2.id, results[0]['payload']['user_id'])

        results = UserMappingType.suggest_completions('r1')
        eq_(1, len(results))
        eq_(u'Rick Róss (r1cky)', results[0]['text'])
        eq_(u1.id, results[0]['payload']['user_id'])

        # Add another Ri....
        u3 = user(username='richard', email='r2@r.com', save=True)
        profile(user=u3, name=u'Richard Smith')

        self.refresh()
        eq_(UserMappingType.search().count(), 3)

        results = UserMappingType.suggest_completions('ri')
        eq_(2, len(results))
        texts = [r['text'] for r in results]
        assert u'Rick Róss (r1cky)' in texts
        assert u'Richard Smith (richard)' in texts
