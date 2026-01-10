import os

from django.core.files import File
from pyquery import PyQuery as pq

from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import GroupProfileFactory
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory, add_permission


class EditGroupProfileTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.group_profile = GroupProfileFactory()
        self.client.login(username=self.user.username, password="testpass")

    def _verify_get_and_post(self):
        slug = self.group_profile.slug
        # Verify GET
        r = self.client.get(reverse("groups.edit", args=[slug]), follow=True)
        self.assertEqual(r.status_code, 200)
        # Verify POST
        r = self.client.post(
            reverse("groups.edit", locale="en-US", args=[slug]), {"information": "=new info="}
        )
        self.assertEqual(r.status_code, 302)
        gp = GroupProfile.objects.get(slug=slug)
        self.assertEqual(gp.information, "=new info=")

    def test_edit_with_perm(self):
        add_permission(self.user, GroupProfile, "change_groupprofile")
        self._verify_get_and_post()

    def test_edit_as_leader(self):
        self.group_profile.leaders.add(self.user)
        self._verify_get_and_post()

    def test_edit_without_perm(self):
        slug = self.group_profile.slug
        # Try GET
        r = self.client.get(reverse("groups.edit", args=[slug]), follow=True)
        self.assertEqual(r.status_code, 403)
        # Try POST
        r = self.client.post(
            reverse("groups.edit", locale="en-US", args=[slug]), {"information": "=new info="}
        )
        self.assertEqual(r.status_code, 403)


class EditAvatarTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        add_permission(self.user, GroupProfile, "change_groupprofile")
        self.group_profile = GroupProfileFactory()
        self.client.login(username=self.user.username, password="testpass")

    def tearDown(self):
        if self.group_profile.avatar:
            self.group_profile.avatar.delete()
        super().tearDown()

    def test_upload_avatar(self):
        """Upload a group avatar."""
        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            self.group_profile.avatar.save("test_old.jpg", File(f), save=True)
        assert self.group_profile.avatar.name.endswith("92b516.jpg")
        old_path = self.group_profile.avatar.path
        assert os.path.exists(old_path), "Old avatar is not in place."

        url = reverse("groups.edit_avatar", locale="en-US", args=[self.group_profile.slug])
        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            r = self.client.post(url, {"avatar": f})

        self.assertEqual(302, r.status_code)
        url = reverse("groups.profile", args=[self.group_profile.slug])
        self.assertEqual(url, r["location"])
        assert not os.path.exists(old_path), "Old avatar was not removed."

    def test_delete_avatar(self):
        """Delete a group avatar."""
        self.test_upload_avatar()

        url = reverse("groups.delete_avatar", locale="en-US", args=[self.group_profile.slug])
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        r = self.client.post(url)
        self.assertEqual(302, r.status_code)
        url = reverse("groups.profile", args=[self.group_profile.slug])
        self.assertEqual(url, r["location"])
        gp = GroupProfile.objects.get(slug=self.group_profile.slug)
        self.assertEqual("", gp.avatar.name)


class AddRemoveMemberTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.member = UserFactory()
        add_permission(self.user, GroupProfile, "change_groupprofile")
        self.group_profile = GroupProfileFactory()
        self.client.login(username=self.user.username, password="testpass")

    def test_add_member(self):
        url = reverse("groups.add_member", locale="en-US", args=[self.group_profile.slug])
        r = self.client.get(url)
        self.assertEqual(405, r.status_code)
        r = self.client.post(url, {"users": self.member.username})
        self.assertEqual(302, r.status_code)
        assert self.member in self.group_profile.group.user_set.all()

    def test_remove_member(self):
        self.member.groups.add(self.group_profile.group)
        url = reverse(
            "groups.remove_member", locale="en-US", args=[self.group_profile.slug, self.member.id]
        )
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        r = self.client.post(url)
        self.assertEqual(302, r.status_code)
        assert self.member not in self.group_profile.group.user_set.all()


class AddRemoveLeaderTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        add_permission(self.user, GroupProfile, "change_groupprofile")
        self.leader = UserFactory()
        self.group_profile = GroupProfileFactory()
        self.client.login(username=self.user.username, password="testpass")

    def test_add_leader(self):
        url = reverse("groups.add_leader", locale="en-US", args=[self.group_profile.slug])
        r = self.client.get(url)
        self.assertEqual(405, r.status_code)
        r = self.client.post(url, {"users": self.leader.username})
        self.assertEqual(302, r.status_code)
        assert self.leader in self.group_profile.leaders.all()

    def test_remove_member(self):
        self.group_profile.leaders.add(self.leader)
        url = reverse(
            "groups.remove_leader", locale="en-US", args=[self.group_profile.slug, self.leader.id]
        )
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        r = self.client.post(url)
        self.assertEqual(302, r.status_code)
        assert self.leader not in self.group_profile.leaders.all()


class JoinContributorsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="testpass")
        GroupFactory(name="Contributors")

    def test_join_contributors(self):
        next = reverse("groups.list")
        url = reverse("groups.join_contributors", locale="en-US")
        url = urlparams(url, next=next)
        r = self.client.get(url)
        self.assertEqual(405, r.status_code)
        r = self.client.post(url)
        self.assertEqual(302, r.status_code)
        self.assertEqual(next, r["location"])
        assert self.user.groups.filter(name="Contributors").exists()


class PrivateGroupTests(TestCase):
    """Tests for private group visibility and access control."""

    def setUp(self):
        super().setUp()
        self.regular_user = UserFactory()
        self.member_user = UserFactory()
        self.leader_user = UserFactory()
        self.superuser = UserFactory(is_superuser=True, is_staff=True)

        self.private_group1 = GroupProfileFactory(is_private=True)
        self.private_group1.group.user_set.add(self.member_user)
        self.private_group1.leaders.add(self.leader_user)
        self.private_group2 = GroupProfileFactory(is_private=True)
        self.public_group1 = GroupProfileFactory(is_private=False)
        self.public_group2 = GroupProfileFactory(is_private=False)

        # Ensure that the Staff Content Team group profile has a slug.
        self.staff_content_group = GroupProfile.objects.get(group__name="Staff Content Team")
        self.staff_content_group.save()

    def test_public_group_visible_to_all(self):
        """Public groups should be visible to everyone."""
        # Anonymous viewer
        resp = self.client.get(
            reverse("groups.profile", kwargs={"group_slug": self.public_group1.slug})
        )
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(
            reverse("groups.profile", kwargs={"group_slug": self.public_group2.slug})
        )
        self.assertEqual(resp.status_code, 200)

        # Regular user
        self.client.login(username=self.regular_user.username, password="testpass")
        resp = self.client.get(
            reverse("groups.profile", kwargs={"group_slug": self.public_group1.slug})
        )
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(
            reverse("groups.profile", kwargs={"group_slug": self.public_group2.slug})
        )
        self.assertEqual(resp.status_code, 200)

    def test_private_group_returns_404_for_anonymous(self):
        """Private groups should return 404 for anonymous users."""
        resp = self.client.get(
            reverse("groups.profile", kwargs={"group_slug": self.private_group1.slug})
        )
        self.assertEqual(resp.status_code, 404)

    def test_private_group_returns_404_for_non_members(self):
        """Private groups should return 404 for non-members."""
        self.client.login(username=self.regular_user.username, password="testpass")
        resp = self.client.get(
            reverse("groups.profile", kwargs={"group_slug": self.private_group1.slug})
        )
        self.assertEqual(resp.status_code, 404)

    def test_private_group_visible_to_members(self):
        """Private groups should be visible to members."""
        self.client.login(username=self.member_user.username, password="testpass")
        resp = self.client.get(
            reverse("groups.profile", kwargs={"group_slug": self.private_group1.slug})
        )
        self.assertEqual(resp.status_code, 200)

    def test_private_group_visible_to_leaders(self):
        """Private groups should be visible to leaders."""
        self.client.login(username=self.leader_user.username, password="testpass")
        resp = self.client.get(
            reverse("groups.profile", kwargs={"group_slug": self.private_group1.slug})
        )
        self.assertEqual(resp.status_code, 200)

    def test_private_group_visible_to_superusers(self):
        """Private groups should be visible to superusers."""
        self.client.login(username=self.superuser.username, password="testpass")
        resp = self.client.get(
            reverse("groups.profile", kwargs={"group_slug": self.private_group1.slug})
        )
        self.assertEqual(resp.status_code, 200)

    def test_private_group_edit_returns_404_for_users_without_access(self):
        """Edit view should return 404 for private groups to users without access."""
        self.client.login(username=self.regular_user.username, password="testpass")
        resp = self.client.get(
            reverse("groups.edit", kwargs={"group_slug": self.private_group1.slug})
        )
        self.assertEqual(resp.status_code, 404)

    def test_private_group_avatar_edit_returns_404(self):
        """Avatar edit should return 404 for private groups to users without access."""
        self.client.login(username=self.regular_user.username, password="testpass")
        resp = self.client.get(
            reverse("groups.edit_avatar", kwargs={"group_slug": self.private_group1.slug})
        )
        self.assertEqual(resp.status_code, 404)

    def test_private_group_avatar_delete_returns_404(self):
        """Avatar delete should return 404 for private groups to users without access."""
        self.client.login(username=self.regular_user.username, password="testpass")
        resp = self.client.get(
            reverse("groups.delete_avatar", kwargs={"group_slug": self.private_group1.slug})
        )
        self.assertEqual(resp.status_code, 404)

    def test_private_group_add_member_returns_404(self):
        """Add member should return 404 for private groups to non-members."""
        self.client.login(username=self.regular_user.username, password="testpass")
        resp = self.client.post(
            reverse("groups.add_member", kwargs={"group_slug": self.private_group1.slug}),
            {"users": "testuser"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_private_group_remove_member_returns_404(self):
        """Remove member should return 404 for private groups to non-members."""
        self.client.login(username=self.regular_user.username, password="testpass")
        resp = self.client.get(
            reverse(
                "groups.remove_member",
                kwargs={"group_slug": self.private_group1.slug, "user_id": self.member_user.id},
            )
        )
        self.assertEqual(resp.status_code, 404)

    def test_private_group_add_leader_returns_404(self):
        """Add leader should return 404 for private groups to non-members."""
        self.client.login(username=self.regular_user.username, password="testpass")
        resp = self.client.post(
            reverse("groups.add_leader", kwargs={"group_slug": self.private_group1.slug}),
            {"users": "testuser"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_private_group_remove_leader_returns_404(self):
        """Remove leader should return 404 for private groups to non-members."""
        self.client.login(username=self.regular_user.username, password="testpass")
        resp = self.client.get(
            reverse(
                "groups.remove_leader",
                kwargs={"group_slug": self.private_group1.slug, "user_id": self.leader_user.id},
            )
        )
        self.assertEqual(resp.status_code, 404)

    def test_list_excludes_private_groups_for_anonymous(self):
        """List view should exclude private groups for anonymous users."""
        resp = self.client.get(reverse("groups.list"))
        self.assertEqual(resp.status_code, 200)
        doc = pq(resp.content)
        self.assertEqual(len(doc('a[href^="/en-US/groups/"]')), 3)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.public_group1.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.public_group2.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.staff_content_group.slug}/"]')), 1)

    def test_list_excludes_private_groups_for_non_members(self):
        """List view should exclude private groups for non-members."""
        self.client.login(username=self.regular_user.username, password="testpass")
        resp = self.client.get(reverse("groups.list"))
        self.assertEqual(resp.status_code, 200)
        doc = pq(resp.content)
        self.assertEqual(len(doc('a[href^="/en-US/groups/"]')), 3)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.public_group1.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.public_group2.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.staff_content_group.slug}/"]')), 1)

    def test_list_includes_private_groups_for_members(self):
        """List view should include private groups for members."""
        self.client.login(username=self.member_user.username, password="testpass")
        resp = self.client.get(reverse("groups.list"))
        self.assertEqual(resp.status_code, 200)
        doc = pq(resp.content)
        self.assertEqual(len(doc('a[href^="/en-US/groups/"]')), 4)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.private_group1.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.public_group1.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.public_group2.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.staff_content_group.slug}/"]')), 1)

    def test_list_includes_all_groups_for_superusers(self):
        """List view should include all groups for superusers."""
        self.client.login(username=self.superuser.username, password="testpass")
        resp = self.client.get(reverse("groups.list"))
        self.assertEqual(resp.status_code, 200)
        doc = pq(resp.content)
        self.assertEqual(len(doc('a[href^="/en-US/groups/"]')), 5)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.private_group1.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.private_group2.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.public_group1.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.public_group2.slug}/"]')), 1)
        self.assertEqual(len(doc(f'a[href="/en-US/groups/{self.staff_content_group.slug}/"]')), 1)

    def test_leader_can_edit_private_group(self):
        """Leaders should be able to edit private groups."""
        self.client.login(username=self.leader_user.username, password="testpass")
        resp = self.client.get(reverse("groups.edit", args=[self.private_group1.slug]))
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(
            reverse("groups.edit", kwargs={"group_slug": self.private_group1.slug}),
            {"information": "Updated info"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            GroupProfile.objects.filter(
                slug=self.private_group1.slug, information="Updated info"
            ).exists()
        )

    def test_member_cannot_edit_private_group(self):
        """Regular members should not be able to edit private groups."""
        self.client.login(username=self.member_user.username, password="testpass")
        resp = self.client.get(
            reverse("groups.edit", kwargs={"group_slug": self.private_group1.slug})
        )
        self.assertEqual(resp.status_code, 403)


class PrivateGroupFormTests(TestCase):
    """Tests for the is_private field in forms."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.group_profile = GroupProfileFactory()
        self.group_profile.leaders.add(self.user)
        self.client.login(username=self.user.username, password="testpass")

    def test_can_toggle_is_private(self):
        """Leaders should be able to toggle is_private through the form."""
        self.assertFalse(self.group_profile.is_private)

        url = reverse("groups.edit", args=[self.group_profile.slug])
        r = self.client.post(url, {"information": "Test info", "is_private": True})
        self.assertEqual(r.status_code, 302)

        self.group_profile.refresh_from_db()
        self.assertTrue(self.group_profile.is_private)
