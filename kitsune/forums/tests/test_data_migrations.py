from importlib import import_module
from unittest import SkipTest

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from kitsune.forums.tests import ForumFactory
from kitsune.users.tests import GroupFactory, UserFactory


class DataMigrationTests(TestCase):
    """Test data migrations."""

    def setUp(self):
        if not (apps.is_installed("authority") and apps.is_installed("guardian")):
            raise SkipTest

        from authority.models import Permission

        self.user1 = user1 = UserFactory()
        self.user2 = user2 = UserFactory()
        self.group = group = GroupFactory()
        group.user_set.add(user2)
        self.forum1 = forum1 = ForumFactory()
        self.forum2 = forum2 = ForumFactory()
        self.forum3 = forum3 = ForumFactory()
        self.forum4 = forum4 = ForumFactory()

        forum_ct = ContentType.objects.get_for_model(forum1)

        for codename in (
            "forums_forum.thread_edit_forum",
            "forums_forum.thread_delete_forum",
            "forums_forum.thread_move_forum",
            "forums_forum.thread_sticky_forum",
            "forums_forum.thread_locked_forum",
            "forums_forum.post_edit_forum",
            "forums_forum.post_delete_forum",
        ):
            Permission(
                approved=True,
                codename=codename,
                content_type=forum_ct,
                object_id=forum1.id,
                user=user1,
            ).save()
            Permission(
                approved=True,
                codename=codename,
                content_type=forum_ct,
                object_id=forum1.id,
                group=group,
            ).save()

        Permission(
            approved=True,
            codename="forums_forum.view_in_forum",
            content_type=forum_ct,
            object_id=forum2.id,
        ).save()
        Permission(
            approved=True,
            codename="forums_forum.post_in_forum",
            content_type=forum_ct,
            object_id=forum2.id,
        ).save()

        Permission(
            approved=True,
            codename="forums_forum.view_in_forum",
            content_type=forum_ct,
            object_id=forum3.id,
            group=group,
        ).save()

        Permission(
            approved=True,
            codename="forums_forum.post_in_forum",
            content_type=forum_ct,
            object_id=forum4.id,
            user=user2,
        ).save()

    def test_authority_to_guardian_data_migration(self):
        from guardian.shortcuts import get_objects_for_group, get_objects_for_user

        migration = import_module("kitsune.forums.migrations.0003_authority_to_guardian_data")

        migration.migrate_authority_to_guardian(apps, None)

        self.forum1.refresh_from_db()
        self.forum2.refresh_from_db()
        self.forum3.refresh_from_db()
        self.forum4.refresh_from_db()

        # Ensure that we've identified the correct forums to restrict.
        self.assertFalse(self.forum1.restrict_viewing)
        self.assertFalse(self.forum1.restrict_posting)
        self.assertTrue(self.forum2.restrict_viewing)
        self.assertTrue(self.forum2.restrict_posting)
        self.assertTrue(self.forum3.restrict_viewing)
        self.assertFalse(self.forum3.restrict_posting)
        self.assertFalse(self.forum4.restrict_viewing)
        self.assertTrue(self.forum4.restrict_posting)

        # Ensure that user1 and group have the following permissions on forum1,
        # remembering that user2 has the same permissions via the group.
        perms = (
            "forums.edit_forum_thread",
            "forums.delete_forum_thread",
            "forums.move_forum_thread",
            "forums.sticky_forum_thread",
            "forums.lock_forum_thread",
            "forums.edit_forum_thread_post",
            "forums.delete_forum_thread_post",
        )
        self.assertEqual(list(get_objects_for_user(self.user1, perms)), [self.forum1])
        self.assertEqual(list(get_objects_for_group(self.group, perms)), [self.forum1])
        # User2 gets the perms via the group.
        self.assertEqual(list(get_objects_for_user(self.user2, perms)), [self.forum1])

        # Ensure that user1 should not have the following permission on any object.
        self.assertEqual(get_objects_for_user(self.user1, "forums.view_in_forum").count(), 0)
        self.assertEqual(get_objects_for_user(self.user1, "forums.post_in_forum").count(), 0)

        # Check the following permissions for the group.
        self.assertEqual(
            list(get_objects_for_group(self.group, "forums.view_in_forum")), [self.forum3]
        )
        self.assertEqual(get_objects_for_group(self.group, "forums.post_in_forum").count(), 0)

        # Check the following permission for user2, remembering that user2 has access
        # to forum3 via the group.
        self.assertEqual(
            list(get_objects_for_user(self.user2, "forums.post_in_forum")), [self.forum4]
        )
        self.assertEqual(
            list(get_objects_for_user(self.user2, "forums.view_in_forum")), [self.forum3]
        )
