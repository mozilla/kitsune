import os

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.files import File
from pyquery import PyQuery as pq

from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import GroupProfileFactory
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory


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

    def test_edit_as_superuser(self):
        self.user.is_superuser = True
        self.user.save()
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
        self.group_profile = GroupProfileFactory()
        self.group_profile.leaders.add(self.user)
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
        self.group_profile = GroupProfileFactory()
        self.group_profile.leaders.add(self.user)
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

    def test_cannot_remove_member_who_is_last_leader(self):
        """Cannot remove a member who is the last leader of a root group."""
        self.user.groups.add(self.group_profile.group)
        self.group_profile.refresh_from_db()
        self.assertEqual(self.group_profile.leaders.count(), 1)

        url = reverse(
            "groups.remove_member", locale="en-US", args=[self.group_profile.slug, self.user.id]
        )
        r = self.client.post(url, follow=True)
        self.assertEqual(200, r.status_code)
        self.assertContains(r, "Cannot remove")
        self.assertContains(r, "last leader")
        assert self.user in self.group_profile.group.user_set.all()
        assert self.user in self.group_profile.leaders.all()


class AddRemoveLeaderTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.leader = UserFactory()
        self.group_profile = GroupProfileFactory()
        self.group_profile.leaders.add(self.user)
        self.client.login(username=self.user.username, password="testpass")

    def test_add_leader(self):
        url = reverse("groups.add_leader", locale="en-US", args=[self.group_profile.slug])
        r = self.client.get(url)
        self.assertEqual(405, r.status_code)
        r = self.client.post(url, {"users": self.leader.username})
        self.assertEqual(302, r.status_code)
        assert self.leader in self.group_profile.leaders.all()

    def test_remove_leader(self):
        self.group_profile.leaders.add(self.leader)
        self.leader.groups.add(self.group_profile.group)
        url = reverse(
            "groups.remove_leader", locale="en-US", args=[self.group_profile.slug, self.leader.id]
        )
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        r = self.client.post(url)
        self.assertEqual(302, r.status_code)
        assert self.leader not in self.group_profile.leaders.all()
        assert self.leader in self.group_profile.group.user_set.all()

    def test_cannot_remove_last_leader_from_root(self):
        """Cannot remove the last leader from a root group."""
        self.group_profile.refresh_from_db()
        self.assertEqual(self.group_profile.leaders.count(), 1)

        url = reverse(
            "groups.remove_leader", locale="en-US", args=[self.group_profile.slug, self.user.id]
        )
        r = self.client.post(url, follow=True)
        self.assertEqual(200, r.status_code)
        self.assertContains(r, "last leader of a root group")
        assert self.user in self.group_profile.leaders.all()

    def test_can_remove_leader_from_subgroup(self):
        """Can remove the only leader from a subgroup."""
        sub_profile = self.group_profile.add_child(group=self.group_profile.group, slug="subgroup")
        sub_leader = UserFactory()
        sub_profile.leaders.add(sub_leader)

        self.user.is_superuser = True
        self.user.save()

        url = reverse(
            "groups.remove_leader", locale="en-US", args=[sub_profile.slug, sub_leader.id]
        )
        r = self.client.post(url)
        self.assertEqual(302, r.status_code)
        assert sub_leader not in sub_profile.leaders.all()


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


class DeactivatedMemberVisibilityTests(TestCase):
    """Test that deactivated users are hidden from group profile for non-privileged viewers."""

    def setUp(self):
        super().setUp()
        self.group_profile = GroupProfileFactory()

        self.active_leader = UserFactory()
        self.group_profile.leaders.add(self.active_leader)
        self.group_profile.group.user_set.add(self.active_leader)

        self.deactivated_leader = UserFactory(is_active=False)
        self.group_profile.leaders.add(self.deactivated_leader)
        self.group_profile.group.user_set.add(self.deactivated_leader)

        self.active_member = UserFactory()
        self.group_profile.group.user_set.add(self.active_member)

        self.deactivated_member = UserFactory(is_active=False)
        self.group_profile.group.user_set.add(self.deactivated_member)

        self.url = reverse("groups.profile", args=[self.group_profile.slug])

    def _get_profile_doc(self):
        r = self.client.get(self.url)
        self.assertEqual(200, r.status_code)
        return pq(r.content)

    def _leader_names(self, doc):
        return {pq(el).text() for el in doc("ul.users.leaders .user-name")}

    def _member_names(self, doc):
        return {pq(el).text() for el in doc("ul.users.members .user-name")}

    def _group_count(self, doc, label):
        for el in doc(".group-stats .stat-item"):
            item = pq(el)
            if item(".stat-label").text() == label:
                return int(item(".stat-value").text())
        raise AssertionError(f"Stat '{label}' not found in .group-stats")

    def test_regular_user_sees_only_active_members(self):
        """A regular (non-leader) user sees only active leaders and members."""
        regular_user = UserFactory()
        self.client.login(username=regular_user.username, password="testpass")
        doc = self._get_profile_doc()
        self.assertEqual(self._leader_names(doc), {self.active_leader.profile.display_name})
        self.assertEqual(
            self._member_names(doc),
            {self.active_leader.profile.display_name, self.active_member.profile.display_name},
        )
        self.assertEqual(self._group_count(doc, "Leaders"), 1)
        self.assertEqual(self._group_count(doc, "Members"), 2)

    def test_staff_user_sees_all_members(self):
        """A user with is_staff=True sees both active and deactivated leaders/members."""
        staff_user = UserFactory(is_staff=True)
        self.client.login(username=staff_user.username, password="testpass")
        doc = self._get_profile_doc()

        self.assertEqual(
            self._leader_names(doc),
            {
                self.active_leader.profile.display_name,
                self.deactivated_leader.profile.display_name,
            },
        )
        self.assertEqual(
            self._member_names(doc),
            {
                self.active_leader.profile.display_name,
                self.deactivated_leader.profile.display_name,
                self.active_member.profile.display_name,
                self.deactivated_member.profile.display_name,
            },
        )
        self.assertEqual(self._group_count(doc, "Leaders"), 2)
        self.assertEqual(self._group_count(doc, "Members"), 4)

    def test_staff_group_member_sees_all_members(self):
        """A member of the Staff group sees both active and deactivated leaders/members."""
        staff_group, _ = Group.objects.get_or_create(name=settings.STAFF_GROUP)
        staff_group_member = UserFactory()
        staff_group_member.groups.add(staff_group)
        self.client.login(username=staff_group_member.username, password="testpass")
        doc = self._get_profile_doc()
        self.assertEqual(
            self._leader_names(doc),
            {
                self.active_leader.profile.display_name,
                self.deactivated_leader.profile.display_name,
            },
        )
        self.assertEqual(
            self._member_names(doc),
            {
                self.active_leader.profile.display_name,
                self.deactivated_leader.profile.display_name,
                self.active_member.profile.display_name,
                self.deactivated_member.profile.display_name,
            },
        )
        self.assertEqual(self._group_count(doc, "Leaders"), 2)
        self.assertEqual(self._group_count(doc, "Members"), 4)

    def test_group_leader_sees_all_members(self):
        """A direct leader of the group sees both active and deactivated leaders/members."""
        self.client.login(username=self.active_leader.username, password="testpass")
        doc = self._get_profile_doc()
        self.assertEqual(
            self._leader_names(doc),
            {
                self.active_leader.profile.display_name,
                self.deactivated_leader.profile.display_name,
            },
        )
        self.assertEqual(
            self._member_names(doc),
            {
                self.active_leader.profile.display_name,
                self.deactivated_leader.profile.display_name,
                self.active_member.profile.display_name,
                self.deactivated_member.profile.display_name,
            },
        )
        self.assertEqual(self._group_count(doc, "Leaders"), 2)
        self.assertEqual(self._group_count(doc, "Members"), 4)
