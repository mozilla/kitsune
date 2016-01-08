from django.contrib.contenttypes.models import ContentType
from django.test.client import RequestFactory

from kitsune.access.templatetags.jinja_helpers import has_perm, has_perm_or_owns
from kitsune.access.tests import PermissionFactory
from kitsune.forums.tests import ForumTestCase, ForumFactory, ThreadFactory
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory, GroupFactory


class ForumTestPermissions(ForumTestCase):
    """Make sure access helpers work on the forums."""

    def setUp(self):
        url = reverse('forums.threads', args=[u'test-forum'])
        self.context = {'request': RequestFactory().get(url)}

        self.group = GroupFactory()

        # Set up forum_1
        f = self.forum_1 = ForumFactory()
        ct = ContentType.objects.get_for_model(self.forum_1)
        permission_names = [
            'forums_forum.thread_edit_forum',
            'forums_forum.post_edit_forum',
            'forums_forum.post_delete_forum',
            'forums_forum.thread_delete_forum',
            'forums_forum.thread_sticky_forum',
            'forums_forum.thread_move_forum',
        ]
        for name in permission_names:
            PermissionFactory(codename=name, content_type=ct, object_id=f.id, group=self.group)

        # Set up forum_2
        f = self.forum_2 = ForumFactory()
        PermissionFactory(codename='forums_forum.thread_move_forum', content_type=ct,
                          object_id=f.id, group=self.group)

    def test_has_perm_thread_edit(self):
        """User in group can edit thread in forum_1, but not in forum_2."""
        u = UserFactory()
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert has_perm(self.context, 'forums_forum.thread_edit_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_edit_forum',
                            self.forum_2)

    def test_has_perm_or_owns_thread_edit(self):
        """Users can edit their own threads."""
        my_t = ThreadFactory()
        me = my_t.creator
        other_t = ThreadFactory()
        self.context['request'].user = me
        perm = 'forums_forum.thread_edit_forum'
        assert has_perm_or_owns(self.context, perm, my_t, self.forum_1)
        assert not has_perm_or_owns(self.context, perm, other_t, self.forum_1)

    def test_has_perm_thread_delete(self):
        """User in group can delete thread in forum_1, but not in forum_2."""
        u = UserFactory()
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert has_perm(self.context, 'forums_forum.thread_delete_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_delete_forum',
                            self.forum_2)

    def test_has_perm_thread_sticky(self):
        # User in group can change sticky status of thread in forum_1,
        # but not in forum_2.
        u = UserFactory()
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert has_perm(self.context, 'forums_forum.thread_sticky_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_sticky_forum',
                            self.forum_2)

    def test_has_perm_thread_locked(self):
        # Sanity check: user in group has no permission to change
        # locked status in forum_1.
        u = UserFactory()
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert not has_perm(self.context, 'forums_forum.thread_locked_forum',
                            self.forum_1)

    def test_has_perm_post_edit(self):
        """User in group can edit any post in forum_1, but not in forum_2."""
        u = UserFactory()
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert has_perm(self.context, 'forums_forum.post_edit_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.post_edit_forum',
                            self.forum_2)

    def test_has_perm_post_delete(self):
        """User in group can delete posts in forum_1, but not in forum_2."""
        u = UserFactory()
        self.group.user_set.add(u)

        self.context['request'].user = u
        assert has_perm(self.context, 'forums_forum.post_delete_forum',
                        self.forum_1)
        assert not has_perm(self.context, 'forums_forum.post_delete_forum',
                            self.forum_2)

    def test_no_perm_thread_delete(self):
        """User not in group cannot delete thread in any forum."""
        self.context['request'].user = UserFactory()
        assert not has_perm(self.context, 'forums_forum.thread_delete_forum',
                            self.forum_1)
        assert not has_perm(self.context, 'forums_forum.thread_delete_forum',
                            self.forum_2)
