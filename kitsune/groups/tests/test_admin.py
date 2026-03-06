from unittest import mock

from django import forms
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

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
        profile = GroupProfile.add_root(group=group, slug="test-group")

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
        profile = GroupProfile.add_root(group=group, slug="test-group-2")

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
        profile = GroupProfile.add_root(group=group, slug="test-root-group")

        mock_request = self.factory.post("/admin/groups/groupprofile/")
        mock_form = MockForm(profile)

        with self.assertRaises(forms.ValidationError) as cm:
            self.admin.save_related(mock_request, mock_form, [], change=True)

        self.assertIn("Root groups must have at least one leader", str(cm.exception))

    def test_subgroup_can_have_no_leaders(self):
        """Ensure subgroups can be saved without leaders."""
        root_group = Group.objects.create(name="Root Group")
        root_profile = GroupProfile.add_root(group=root_group, slug="root-group")
        root_leader = UserFactory()
        root_profile.leaders.add(root_leader)

        sub_group = Group.objects.create(name="Sub Group")
        sub_profile = root_profile.add_child(group=sub_group, slug="sub-group")

        mock_request = self.factory.post("/admin/groups/groupprofile/")
        mock_form = MockForm(sub_profile)

        self.admin.save_related(mock_request, mock_form, [], change=True)

        self.assertEqual(sub_profile.leaders.count(), 0)

    @mock.patch("kitsune.groups.admin.open_as_pil_image")
    def test_avatar_too_large_pixels(self, mock_open):
        """Uploading an avatar that exceeds pixel limits shows a form validation error."""
        mock_open.side_effect = FileTooLargeError("Image exceeds the maximum allowed size.")

        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            avatar = SimpleUploadedFile("test.jpg", f.read(), content_type="image/jpeg")
        group = Group.objects.create(name="Avatar Test Group")
        profile = GroupProfile.add_root(group=group, slug="avatar-test-group")

        form = GroupProfileAdminForm(
            data={"group": group.pk, "slug": "avatar-test-group"},
            files={"avatar": avatar},
            instance=profile,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)
        self.assertIn("Image exceeds the maximum allowed size.", form.errors["avatar"][0])

    @mock.patch("kitsune.groups.admin.check_file_size")
    def test_avatar_too_large_file_size(self, mock_check):
        """Uploading an avatar that exceeds file size limits shows a form validation error."""
        mock_check.side_effect = FileTooLargeError("File is too large.")

        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            avatar = SimpleUploadedFile("test.jpg", f.read(), content_type="image/jpeg")
        group = Group.objects.create(name="Size Test Group")
        profile = GroupProfile.add_root(group=group, slug="size-test-group")

        form = GroupProfileAdminForm(
            data={"group": group.pk, "slug": "size-test-group"},
            files={"avatar": avatar},
            instance=profile,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)
        self.assertIn("File is too large.", form.errors["avatar"][0])
