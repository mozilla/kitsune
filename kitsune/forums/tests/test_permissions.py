from django.contrib.contenttypes.models import ContentType

import test_utils

from kitsune.access.helpers import has_perm, has_perm_or_owns
from kitsune.access.tests import permission
from kitsune.forums.tests import ForumTestCase, forum, thread
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import user, group


class ForumTestPermissions(ForumTestCase):
    """Make sure access helpers work on the forums."""

    def setUp(self):
        url = reverse('forums.threads', args=[u'test-forum'])
        self.context = {'request': test_utils.RequestFactory().get(url)}

        self.group = group(save=True)

        # Set up forum_1
        f = self.forum_1 = forum(save=True)
        ct = ContentType.objects.get_for_model(self.forum_1)
        permission(codename='forums_forum.thread_edit_forum', content_type=ct,
                   object_id=f.id, group=self.group, save=True)
        permission(codename='forums_forum.post_edit_forum', content_type=ct,
                   object_id=f.id, group=self.group, save=True)
        permission(codename='forums_forum.post_delete_forum', content_type=ct,
                   object_id=f.id, group=self.group, save=True)
        permission(codename='forums_forum.thread_delete_forum',
                   content_type=ct, object_id=f.id, group=self.group,
                   save=True)
        permission(codename='forums_forum.thread_sticky_forum',
                   content_type=ct, object_id=f.id, group=self.group,
                   save=True)
        permission(codename='forums_forum.thread_move_forum', content_type=ct,
                   object_id=f.id, group=self.group, save=True)

        # Set up forum_2
        f = self.forum_2 = forum(save=True)
        permission(codename='forums_forum.thread_move_forum', content_type=ct,
                   object_id=f.id, group=self.group, save=True)

    def test_has_perm_thread_edit(self):
        """User in group can edit thread in forum_1, but not in forum_2."""
        u = user(save=True)
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert has_perm(self.context, 'forums_forum.thread_edit_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_edit_forum',
                            self.forum_2)

    def test_has_perm_or_owns_thread_edit(self):
        """Users can edit their own threads."""
        my_t = thread(save=True)
        me = my_t.creator
        other_t = thread(save=True)
        self.context['request'].user = me
        perm = 'forums_forum.thread_edit_forum'
        assert has_perm_or_owns(self.context, perm, my_t, self.forum_1)
        assert not has_perm_or_owns(self.context, perm, other_t, self.forum_1)

    def test_has_perm_thread_delete(self):
        """User in group can delete thread in forum_1, but not in forum_2."""
        u = user(save=True)
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert has_perm(self.context, 'forums_forum.thread_delete_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_delete_forum',
                            self.forum_2)

    def test_has_perm_thread_sticky(self):
        # User in group can change sticky status of thread in forum_1,
        # but not in forum_2.
        u = user(save=True)
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert has_perm(self.context, 'forums_forum.thread_sticky_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_sticky_forum',
                            self.forum_2)

    def test_has_perm_thread_locked(self):
        # Sanity check: user in group has no permission to change
        # locked status in forum_1.
        u = user(save=True)
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert not has_perm(self.context, 'forums_forum.thread_locked_forum',
                            self.forum_1)

    def test_has_perm_post_edit(self):
        """User in group can edit any post in forum_1, but not in forum_2."""
        u = user(save=True)
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert has_perm(self.context, 'forums_forum.post_edit_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.post_edit_forum',
                            self.forum_2)

    def test_has_perm_post_delete(self):
        """User in group can delete posts in forum_1, but not in forum_2."""
        u = user(save=True)
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert has_perm(self.context, 'forums_forum.post_delete_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.post_delete_forum',
                            self.forum_2)

    def test_no_perm_thread_delete(self):
        """User not in group cannot delete thread in any forum."""
        self.context['request'].user = user(save=True)
        assert not has_perm(self.context, 'forums_forum.thread_delete_forum',
                            self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_delete_forum',
                            self.forum_2)
