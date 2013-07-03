from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from kitsune.access.tests import permission
from kitsune.forums.tests import forum, post, restricted_forum, thread
from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import group, user


class SearchViewTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_discussion_forum_with_restricted_forums(self):
        """Tests who can see restricted forums in search form."""
        # This is a long test, but it saves us from doing the setup
        # twice.
        forum1 = forum(name=u'ou812forum', save=True)
        thread1 = thread(forum=forum1, title=u'audio 2', save=True)
        post(thread=thread1, save=True)

        forum2 = restricted_forum(name=u'restrictedkeepout', save=True)
        thread2 = thread(forum=forum2, title=u'audio 2', save=True)
        post(thread=thread2, save=True)

        self.refresh()

        # Get the Advanced Search Form as an anonymous user
        response = self.client.get(reverse('search'), {'a': '2'})
        eq_(200, response.status_code)

        # Regular forum should show up
        assert 'ou812forum' in response.content

        # Restricted forum should not show up
        assert 'restrictedkeepout' not in response.content

        u = user(save=True)
        g = group(save=True)
        g.user_set.add(u)
        ct = ContentType.objects.get_for_model(forum2)
        permission(codename='forums_forum.view_in_forum', content_type=ct,
                   object_id=forum2.id, group=g, save=True)

        # Get the Advanced Search Form as a logged in user
        self.client.login(username=u.username, password='testpass')
        response = self.client.get(reverse('search'), {'a': '2'})
        eq_(200, response.status_code)

        # Both forums should show up for authorized user
        assert 'ou812forum' in response.content
        assert 'restrictedkeepout' in response.content
