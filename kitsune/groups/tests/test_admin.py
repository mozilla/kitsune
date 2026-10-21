import time
from unittest import mock

from django import forms
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse

from kitsune.groups.admin import GroupProfileAdmin, GroupProfileAdminForm
from kitsune.groups.models import GroupProfile
from kitsune.sumo.tests import TestCase
from kitsune.upload.utils import FileTooLargeError
from kitsune.users.tests import UserFactory


class MockForm:
    """Mock form for testing admin save_related."""

    def __init__(self, instance):
        self.instance = instance
        self.cleaned_data = {}

    def save_m2m(self):
        """Mock save_m2m method required by Django admin."""
        pass


class GroupProfileAdminTests(TestCase):
    """Tests for GroupProfile admin interface."""

    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = GroupProfileAdmin(GroupProfile, self.site)

    def test_leader_added_as_member_via_admin(self):
        """Ensure leaders added via admin are automatically added as members."""
        group = Group.objects.create(name="Test Group")
        profile = GroupProfile.objects.add_root(
            create_kwargs={"group": group, "slug": "test-group"}
        )

        user = UserFactory()
        self.assertFalse(user.groups.filter(pk=group.pk).exists())

        profile.leaders.add(user)

        mock_request = self.factory.post("/admin/groups/groupprofile/")
        mock_form = MockForm(profile)

        self.admin.save_related(mock_request, mock_form, [], change=True)

        self.assertTrue(user.groups.filter(pk=group.pk).exists())

    def test_existing_member_stays_member(self):
        """Ensure existing members who become leaders remain members."""
        group = Group.objects.create(name="Test Group 2")
        profile = GroupProfile.objects.add_root(
            create_kwargs={"group": group, "slug": "test-group-2"}
        )

        user = UserFactory()
        user.groups.add(group)
        self.assertTrue(user.groups.filter(pk=group.pk).exists())

        profile.leaders.add(user)

        mock_request = self.factory.post("/admin/groups/groupprofile/")
        mock_form = MockForm(profile)

        self.admin.save_related(mock_request, mock_form, [], change=True)

        self.assertTrue(user.groups.filter(pk=group.pk).exists())
        self.assertEqual(user.groups.filter(pk=group.pk).count(), 1)

    def test_root_group_requires_leader(self):
        """Ensure root groups cannot be saved without at least one leader."""
        group = Group.objects.create(name="Test Root Group")
        profile = GroupProfile.objects.add_root(
            create_kwargs={"group": group, "slug": "test-root-group"}
        )

        mock_request = self.factory.post("/admin/groups/groupprofile/")
        mock_form = MockForm(profile)

        with self.assertRaises(forms.ValidationError) as cm:
            self.admin.save_related(mock_request, mock_form, [], change=True)

        self.assertIn("Root groups must have at least one leader", str(cm.exception))

    def test_subgroup_can_have_no_leaders(self):
        """Ensure subgroups can be saved without leaders."""
        root_group = Group.objects.create(name="Root Group")
        root_profile = GroupProfile.objects.add_root(
            create_kwargs={"group": root_group, "slug": "root-group"}
        )
        root_leader = UserFactory()
        root_profile.leaders.add(root_leader)

        sub_group = Group.objects.create(name="Sub Group")
        sub_profile = GroupProfile.objects.add_child(
            root_profile, create_kwargs={"group": sub_group, "slug": "sub-group"}
        )

        mock_request = self.factory.post("/admin/groups/groupprofile/")
        mock_form = MockForm(sub_profile)

        self.admin.save_related(mock_request, mock_form, [], change=True)

        self.assertEqual(sub_profile.leaders.count(), 0)

    @mock.patch("kitsune.upload.utils.open_as_pil_image")
    def test_avatar_too_large_pixels(self, mock_open):
        """Uploading an avatar that exceeds pixel limits shows a form validation error."""
        mock_open.side_effect = FileTooLargeError("Image exceeds the maximum allowed size.")

        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            avatar = SimpleUploadedFile("test.jpg", f.read(), content_type="image/jpeg")
        group = Group.objects.create(name="Avatar Test Group")
        profile = GroupProfile.objects.add_root(
            create_kwargs={"group": group, "slug": "avatar-test-group"}
        )

        form = GroupProfileAdminForm(
            data={"group": group.pk, "slug": "avatar-test-group"},
            files={"avatar": avatar},
            instance=profile,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)
        self.assertIn("Image exceeds the maximum allowed size.", form.errors["avatar"][0])

    @mock.patch("kitsune.upload.utils.check_file_size")
    def test_avatar_too_large_file_size(self, mock_check):
        """Uploading an avatar that exceeds file size limits shows a form validation error."""
        mock_check.side_effect = FileTooLargeError("File is too large.")

        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            avatar = SimpleUploadedFile("test.jpg", f.read(), content_type="image/jpeg")
        group = Group.objects.create(name="Size Test Group")
        profile = GroupProfile.objects.add_root(
            create_kwargs={"group": group, "slug": "size-test-group"}
        )

        form = GroupProfileAdminForm(
            data={"group": group.pk, "slug": "size-test-group"},
            files={"avatar": avatar},
            instance=profile,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)
        self.assertIn("File is too large.", form.errors["avatar"][0])


class DeleteConfirmationTests(TestCase):
    """Both admins' delete pages must show and check everything that goes too."""

    def setUp(self):
        self.root = GroupProfile.objects.add_root(
            create_kwargs={"group": Group.objects.create(name="Root"), "slug": "root"}
        )
        self.company = GroupProfile.objects.add_child(
            self.root, create_kwargs={"group": Group.objects.create(name="Acme"), "slug": "acme"}
        )
        self.team = GroupProfile.objects.add_child(
            self.company,
            create_kwargs={"group": Group.objects.create(name="Acme IT"), "slug": "acme-it"},
        )
        self.group_delete_url = reverse("admin:auth_group_delete", args=[self.company.group_id])
        self.profile_delete_url = reverse(
            "admin:groups_groupprofile_delete", args=[self.company.pk]
        )

    def _login(self, user):
        self.client.force_login(user, backend="kitsune.users.auth.SumoOIDCAuthBackend")
        session = self.client.session
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()

    def _staff_with(self, perm):
        app_label, codename = perm.split(".")
        user = UserFactory(is_staff=True)
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )
        return user

    def _group_entry(self, profile):
        url = reverse("admin:auth_group_change", args=[profile.group_id])
        return f'Group: <a href="{url}">{profile.group}</a>'

    def _profile_entry(self, profile):
        url = reverse("admin:groups_groupprofile_change", args=[profile.pk])
        return f'Group profile: <a href="{url}">{profile}</a>'

    def test_group_delete_lists_subgroups(self):
        self._login(UserFactory(is_staff=True, is_superuser=True))

        resp = self.client.get(self.group_delete_url)

        self.assertEqual(resp.status_code, 200)
        for profile in (self.company, self.team):
            self.assertContains(resp, self._group_entry(profile), count=1)
            self.assertContains(resp, self._profile_entry(profile), count=1)
        self.assertNotContains(resp, self._group_entry(self.root))
        self.assertNotContains(resp, self._profile_entry(self.root))
        self.assertEqual(resp.context["perms_lacking"], set())

    def test_group_delete_lists_profile_of_subgroup_kept_elsewhere(self):
        other_root = GroupProfile.objects.add_root(
            create_kwargs={"group": Group.objects.create(name="Other"), "slug": "other"}
        )
        GroupProfile.objects.add_child(
            other_root, create_kwargs={"group": self.team.group, "slug": "acme-it-elsewhere"}
        )
        self._login(UserFactory(is_staff=True, is_superuser=True))

        resp = self.client.get(self.group_delete_url)

        self.assertNotContains(resp, self._group_entry(self.team))
        self.assertContains(resp, "Group profile: Acme IT", count=1)

    def test_group_delete_needs_permission_to_delete_group_profiles(self):
        self._login(self._staff_with("auth.delete_group"))

        resp = self.client.get(self.group_delete_url)
        self.assertEqual(resp.context["perms_lacking"], {"group profile"})

        resp = self.client.post(self.group_delete_url, {"post": "yes"})
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Group.objects.filter(pk=self.company.group_id).exists())
        self.assertTrue(GroupProfile.objects.filter(pk=self.company.pk).exists())

    def test_profile_delete_lists_subgroups_but_not_its_own_group(self):
        self._login(UserFactory(is_staff=True, is_superuser=True))

        resp = self.client.get(self.profile_delete_url)

        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, self._group_entry(self.company))
        self.assertContains(resp, self._group_entry(self.team), count=1)
        self.assertContains(resp, self._profile_entry(self.team), count=1)
        self.assertEqual(resp.context["perms_lacking"], set())

    def test_profile_delete_needs_permission_to_delete_groups(self):
        self._login(self._staff_with("groups.delete_groupprofile"))

        resp = self.client.get(self.profile_delete_url)
        self.assertEqual(resp.context["perms_lacking"], {"group"})

        resp = self.client.post(self.profile_delete_url, {"post": "yes"})
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(GroupProfile.objects.filter(pk=self.company.pk).exists())
        self.assertTrue(Group.objects.filter(pk=self.team.group_id).exists())
