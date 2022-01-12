from django.contrib.contenttypes.models import ContentType
from django.test.client import RequestFactory

import factory
from authority.models import Permission
from nose.tools import eq_

from kitsune.access import utils as access
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory


class PermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Permission

    approved = True


class AccessTests(TestCase):
    """Test stuff in access/__init__.py"""

    def setUp(self):
        url = reverse("forums.threads", args=["test-forum"])
        self.context = {"request": RequestFactory().get(url)}

    def test_admin_perm_thread(self):
        """Super user can do anything on any forum."""
        from kitsune.forums.tests import RestrictedForumFactory

        f1 = RestrictedForumFactory()
        f2 = RestrictedForumFactory()

        admin = UserFactory(is_staff=True, is_superuser=True)

        # Loop over all forums perms and both forums
        perms = (
            "thread_edit_forum",
            "thread_delete_forum",
            "post_edit_forum",
            "thread_sticky_forum",
            "thread_locked_forum",
            "post_delete_forum",
            "view_in_forum",
        )

        for perm in perms:
            for forum in [f1, f2]:
                assert access.has_perm(admin, "forums_forum." + perm, forum)

    def test_util_has_perm_or_owns_sanity(self):
        """Sanity check for access.has_perm_or_owns."""
        from kitsune.forums.tests import ThreadFactory

        me = UserFactory()
        my_t = ThreadFactory(creator=me)
        other_t = ThreadFactory()
        perm = "forums_forum.thread_edit_forum"
        allowed = access.has_perm_or_owns(me, perm, my_t, my_t.forum)
        eq_(allowed, True)
        allowed = access.has_perm_or_owns(me, perm, other_t, other_t.forum)
        eq_(allowed, False)

    def test_has_perm_per_object(self):
        """Assert has_perm checks per-object permissions correctly."""
        from kitsune.forums.tests import RestrictedForumFactory

        f1 = RestrictedForumFactory()
        f2 = RestrictedForumFactory()

        # Give user permission to one of the forums
        u = UserFactory()
        perm = "forums_forum.view_in_forum"
        ct = ContentType.objects.get_for_model(f1)
        PermissionFactory(codename=perm, content_type=ct, object_id=f1.id, user=u)
        assert access.has_perm(u, perm, f1)
        assert not access.has_perm(u, perm, f2)

    def test_perm_is_defined_on(self):
        """Test permission relationship

        Test whether we check for permission relationship, independent
        of whether the permission is actually assigned to anyone.
        """
        from kitsune.forums.tests import ForumFactory, RestrictedForumFactory

        f1 = RestrictedForumFactory()
        f2 = ForumFactory()
        perm = "forums_forum.view_in_forum"
        assert access.perm_is_defined_on(perm, f1)
        assert not access.perm_is_defined_on(perm, f2)
