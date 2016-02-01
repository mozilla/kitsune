from django.conf import settings
from django.contrib.auth.models import Permission as DjangoPermission
from django.contrib.auth.models import Group
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

import authority
from authority import permissions
from authority.models import Permission
from authority.exceptions import NotAModel, UnsavedModelInstance
from authority.compat import get_user_model

# Load the form
from authority.forms import UserPermissionForm  # noqa

from kitsune.users.tests import UserFactory


User = get_user_model()


class UserPermission(permissions.BasePermission):
    checks = ('browse',)
    label = 'user_permission'
authority.register(User, UserPermission)


class GroupPermission(permissions.BasePermission):
    checks = ('browse',)
    label = 'group_permission'
authority.register(Group, GroupPermission)


class DjangoPermissionChecksTestCase(TestCase):
    """
    Django permission objects have certain methods that are always present,
    test those here.

    self.user will be given:
    - django permission add_user (test_add)
    - authority to delete_user which is him (test_delete)

    This permissions are given in the test case and not in the fixture, for
    later reference.
    """

    def setUp(self):
        self.user = UserFactory()
        self.check = UserPermission(self.user)

    def test_no_permission(self):
        self.assertFalse(self.check.add_user())
        self.assertFalse(self.check.delete_user())
        self.assertFalse(self.check.delete_user(self.user))

    def test_add(self):
        # setup
        perm = DjangoPermission.objects.get(codename='add_user')
        self.user.user_permissions.add(perm)

        # test
        self.assertTrue(self.check.add_user())

    def test_delete(self):
        perm = Permission(
            user=self.user,
            content_object=self.user,
            codename='user_permission.delete_user',
            approved=True
        )
        perm.save()

        # test
        self.assertFalse(self.check.delete_user())
        self.assertTrue(self.check.delete_user(self.user))


class AssignBehaviourTest(TestCase):
    """
    self.user will be given:
    - permission add_user (test_add),
    - permission delete_user for him (test_delete),
    - all existing codenames permissions: a/b/c/d (test_all),
    """

    def setUp(self):
        self.user = UserFactory()
        self.check = UserPermission(self.user)

    def test_add(self):
        result = self.check.assign(check='add_user')

        self.assertTrue(isinstance(result[0], DjangoPermission))
        self.assertTrue(self.check.add_user())

    def test_delete(self):
        result = self.check.assign(
            content_object=self.user,
            check='delete_user',
        )

        self.assertTrue(isinstance(result[0], Permission))
        self.assertFalse(self.check.delete_user())
        self.assertTrue(self.check.delete_user(self.user))

    def test_all(self):
        result = self.check.assign(content_object=self.user)
        self.assertTrue(isinstance(result, list))
        self.assertTrue(self.check.browse_user(self.user))
        self.assertTrue(self.check.delete_user(self.user))
        self.assertTrue(self.check.add_user(self.user))
        self.assertTrue(self.check.change_user(self.user))


class GenericAssignBehaviourTest(TestCase):
    """
    self.user will be given:
    - permission add (test_add),
    - permission delete for him (test_delete),
    """

    def setUp(self):
        self.user = UserFactory()
        self.check = UserPermission(self.user)

    def test_add(self):
        result = self.check.assign(check='add', generic=True)

        self.assertTrue(isinstance(result[0], DjangoPermission))
        self.assertTrue(self.check.add_user())

    def test_delete(self):
        result = self.check.assign(
            content_object=self.user,
            check='delete',
            generic=True,
        )

        self.assertTrue(isinstance(result[0], Permission))
        self.assertFalse(self.check.delete_user())
        self.assertTrue(self.check.delete_user(self.user))


class AssignExceptionsTest(TestCase):
    """
    Tests that exceptions are thrown if assign() was called with inconsistent
    arguments.
    """

    def setUp(self):
        self.user = UserFactory()
        self.check = UserPermission(self.user)

    def test_unsaved_model(self):
        try:
            self.check.assign(content_object=User())
        except UnsavedModelInstance:
            return True
        self.fail()

    def test_not_model_content_object(self):
        try:
            self.check.assign(content_object='fail')
        except NotAModel:
            return True
        self.fail()


class SmartCachingTestCase(TestCase):
    """
    The base test case for all tests that have to do with smart caching.
    """

    def setUp(self):
        # Create a user.
        self.user = UserFactory()

        # Create a group.
        self.group = Group.objects.create()
        self.group.user_set.add(self.user)

        # Make the checks
        self.user_check = UserPermission(user=self.user)
        self.group_check = GroupPermission(group=self.group)

        # Ensure we are using the smart cache.
        settings.AUTHORITY_USE_SMART_CACHE = True

    def tearDown(self):
        ContentType.objects.clear_cache()

    def _old_user_permission_check(self):
        # This is what the old, pre-cache system would check to see if a user
        # had a given permission.
        return Permission.objects.user_permissions(
            self.user,
            'foo',
            self.user,
            approved=True,
            check_groups=True,
        )

    def _old_group_permission_check(self):
        # This is what the old, pre-cache system would check to see if a user
        # had a given permission.
        return Permission.objects.group_permissions(
            self.group,
            'foo',
            self.group,
            approved=True,
        )


class PerformanceTest(SmartCachingTestCase):
    """
    Tests that permission are actually cached and that the number of queries
    stays constant.
    """

    def test_has_user_perms(self):
        # Show that when calling has_user_perms multiple times no additional
        # queries are done.

        # Make sure the has_user_perms check does not get short-circuited.
        assert not self.user.is_superuser
        assert self.user.is_active

        # Regardless of how many times has_user_perms is called, the number of
        # queries is the same.
        # Content type and permissions (2 queries)
        with self.assertNumQueries(3):
            for _ in range(5):
                # Need to assert it so the query actually gets executed.
                assert not self.user_check.has_user_perms(
                    'foo',
                    self.user,
                    True,
                    False,
                )

    def test_group_has_perms(self):
        with self.assertNumQueries(2):
            for _ in range(5):
                assert not self.group_check.has_group_perms(
                    'foo',
                    self.group,
                    True,
                )

    def test_has_user_perms_check_group(self):
        # Regardless of the number groups permissions, it should only take one
        # query to check both users and groups.
        # Content type and permissions (2 queries)
        with self.assertNumQueries(3):
            self.user_check.has_user_perms(
                'foo',
                self.user,
                approved=True,
                check_groups=True,
            )

    def test_invalidate_user_permissions_cache(self):
        # Show that calling invalidate_permissions_cache will cause extra
        # queries.
        # For each time invalidate_permissions_cache gets called, you
        # will need to do one query to get content type and one to get
        # the permissions.
        with self.assertNumQueries(6):
            for _ in range(5):
                assert not self.user_check.has_user_perms(
                    'foo',
                    self.user,
                    True,
                    False,
                )

            # Invalidate the cache to show that a query will be generated when
            # checking perms again.
            self.user_check.invalidate_permissions_cache()
            ContentType.objects.clear_cache()

            # One query to re generate the cache.
            for _ in range(5):
                assert not self.user_check.has_user_perms(
                    'foo',
                    self.user,
                    True,
                    False,
                )

    def test_invalidate_group_permissions_cache(self):
        # Show that calling invalidate_permissions_cache will cause extra
        # queries.
        # For each time invalidate_permissions_cache gets called, you
        # will need to do one query to get content type and one to get
        with self.assertNumQueries(4):
            for _ in range(5):
                assert not self.group_check.has_group_perms(
                    'foo',
                    self.group,
                    True,
                )

            # Invalidate the cache to show that a query will be generated when
            # checking perms again.
            self.group_check.invalidate_permissions_cache()
            ContentType.objects.clear_cache()

            # One query to re generate the cache.
            for _ in range(5):
                assert not self.group_check.has_group_perms(
                    'foo',
                    self.group,
                    True,
                )

    def test_has_user_perms_check_group_multiple(self):
        # Create a permission with just a group.
        Permission.objects.create(
            content_type=Permission.objects.get_content_type(User),
            object_id=self.user.pk,
            codename='foo',
            group=self.group,
            approved=True,
        )
        # By creating the Permission objects the Content type cache
        # gets created.

        # Check the number of queries.
        with self.assertNumQueries(2):
            assert self.user_check.has_user_perms('foo', self.user, True, True)

        # Create a second group.
        new_group = Group.objects.create(name='new_group')
        new_group.user_set.add(self.user)

        # Create a permission object for it.
        Permission.objects.create(
            content_type=Permission.objects.get_content_type(User),
            object_id=self.user.pk,
            codename='foo',
            group=new_group,
            approved=True,
        )

        self.user_check.invalidate_permissions_cache()

        # Make sure it is the same number of queries.
        with self.assertNumQueries(2):
            assert self.user_check.has_user_perms('foo', self.user, True, True)


class GroupPermissionCacheTestCase(SmartCachingTestCase):
    """
    Tests that peg expected behaviour
    """

    def test_has_user_perms_with_groups(self):
        perms = self._old_user_permission_check()
        self.assertEqual([], list(perms))

        # Use the new cached user perms to show that the user does not have the
        # perms.
        can_foo_with_group = self.user_check.has_user_perms(
            'foo',
            self.user,
            approved=True,
            check_groups=True,
        )
        self.assertFalse(can_foo_with_group)

        # Create a permission with just that group.
        perm = Permission.objects.create(
            content_type=Permission.objects.get_content_type(User),
            object_id=self.user.pk,
            codename='foo',
            group=self.group,
            approved=True,
        )

        # Old permission check
        perms = self._old_user_permission_check()
        self.assertEqual([perm], list(perms))

        # Invalidate the cache.
        self.user_check.invalidate_permissions_cache()
        can_foo_with_group = self.user_check.has_user_perms(
            'foo',
            self.user,
            approved=True,
            check_groups=True,
        )
        self.assertTrue(can_foo_with_group)

    def test_has_group_perms_no_user(self):
        # Make sure calling has_user_perms on a permission that does not have a
        # user does not throw any errors.
        can_foo_with_group = self.group_check.has_group_perms(
            'foo',
            self.user,
            approved=True,
        )
        self.assertFalse(can_foo_with_group)

        perms = self._old_group_permission_check()
        self.assertEqual([], list(perms))

        # Create a permission with just that group.
        perm = Permission.objects.create(
            content_type=Permission.objects.get_content_type(Group),
            object_id=self.group.pk,
            codename='foo',
            group=self.group,
            approved=True,
        )

        # Old permission check
        perms = self._old_group_permission_check()
        self.assertEqual([perm], list(perms))

        # Invalidate the cache.
        self.group_check.invalidate_permissions_cache()

        can_foo_with_group = self.group_check.has_group_perms(
            'foo',
            self.group,
            approved=True,
        )
        self.assertTrue(can_foo_with_group)
