import os
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group
from django.core.files import File
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from django.utils import timezone
from pyquery import PyQuery as pq

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportContractFactory,
    SupportCoverageFactory,
    ZendeskConfigFactory,
)
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory


class GroupListSubgroupCountTests(TestCase):
    """Subgroup counts on the list page respect visibility and isolation."""

    def setUp(self):
        super().setUp()
        # Build: root_a (private, isolated) -> [sub_b, sub_d] -> sub_d -> [sub_e, sub_f]
        self.root_a = GroupProfile.objects.add_root(
            create_kwargs={
                "group": Group.objects.create(name="Root A"),
                "slug": "root-a",
                "visibility": GroupProfile.Visibility.PRIVATE,
                "isolation_enabled": True,
            }
        )
        self.sub_b = GroupProfile.objects.add_child(
            self.root_a,
            create_kwargs={"group": Group.objects.create(name="Sub B"), "slug": "sub-b"},
        )
        self.sub_d = GroupProfile.objects.add_child(
            self.root_a,
            create_kwargs={"group": Group.objects.create(name="Sub D"), "slug": "sub-d"},
        )
        self.sub_e = GroupProfile.objects.add_child(
            self.sub_d,
            create_kwargs={"group": Group.objects.create(name="Sub E"), "slug": "sub-e"},
        )
        self.sub_f = GroupProfile.objects.add_child(
            self.sub_d,
            create_kwargs={"group": Group.objects.create(name="Sub F"), "slug": "sub-f"},
        )

        self.member = UserFactory()
        self.member.groups.add(self.sub_e.group)

    def _get_groups_by_id(self):
        from kitsune.groups import views as groups_views

        request = RequestFactory().get(reverse("groups.list"))
        request.user = self.member
        with mock.patch("kitsune.groups.views.render", return_value=HttpResponse()) as mock_render:
            groups_views.list(request)
        groups = mock_render.call_args.args[2]["groups"]
        return {g.id: g for g in groups}

    def test_isolated_member_sees_filtered_subgroup_counts(self):
        """An isolated member should see counts of only their visible subgroups."""
        groups_by_id = self._get_groups_by_id()

        # root_a has 2 real children (sub_b, sub_d) but member can only see sub_d
        self.assertEqual(groups_by_id[self.root_a.id].visible_numchild, 1)
        # sub_d has 2 real children (sub_e, sub_f) but member can only see sub_e
        self.assertEqual(groups_by_id[self.sub_d.id].visible_numchild, 1)


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

    @override_settings(IMAGE_MAX_PIXELS=1)
    def test_upload_avatar_too_large(self):
        """Uploading an avatar that exceeds IMAGE_MAX_PIXELS fails form validation."""
        url = reverse("groups.edit_avatar", locale="en-US", args=[self.group_profile.slug])
        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            r = self.client.post(url, {"avatar": f})
        self.assertEqual(200, r.status_code)

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
        sub_profile = GroupProfile.objects.add_child(
            self.group_profile,
            create_kwargs={"group": self.group_profile.group, "slug": "subgroup"},
        )
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


class MemberOrderingTests(TestCase):
    """Leaders and members are listed in alphabetical order of their displayed name."""

    def setUp(self):
        super().setUp()
        self.group_profile = GroupProfileFactory()

        # Added in reverse of the expected order, and usernames sort differently
        # from displayed names, so sorting by the wrong thing fails here.
        users = {
            "Carol": None,
            "alice": "carla",
            "Bob": "",
            "zoe": "Aaron",
        }
        for username, display_name in users.items():
            user = UserFactory(username=username, profile__name=display_name)
            self.group_profile.group.user_set.add(user)
            if username in ("zoe", "Bob", "alice"):
                self.group_profile.leaders.add(user)

        # No profile row at all: must fall back to the username, not be dropped.
        self.group_profile.group.user_set.add(UserFactory(username="quinn", profile=None))

        self.url = reverse("groups.profile", args=[self.group_profile.slug])

    def _names(self, section):
        r = self.client.get(self.url)
        self.assertEqual(200, r.status_code)
        return [pq(el).text() for el in pq(r.content)(f"ul.users.{section} .user-name")]

    def test_members_sorted_by_displayed_name(self):
        self.assertEqual(self._names("members"), ["Aaron", "Bob", "carla", "Carol", "quinn"])

    def test_leaders_sorted_by_displayed_name(self):
        self.assertEqual(self._names("leaders"), ["Aaron", "Bob", "carla"])


class MemberOrderingTieBreakTests(TestCase):
    """Users sharing a displayed name fall back to username order, not a random one."""

    def setUp(self):
        super().setUp()
        self.group_profile = GroupProfileFactory()

        # Everyone shows the same name, and they're created in reverse username
        # order, so leaving the tie to the database would list them backwards.
        for username in ("zeta", "mike", "alpha"):
            user = UserFactory(username=username, profile__name="Alex Smith")
            self.group_profile.group.user_set.add(user)
            self.group_profile.leaders.add(user)

        self.url = reverse("groups.profile", args=[self.group_profile.slug])

    def _usernames(self, section):
        """The usernames behind each row, read from the profile links."""
        r = self.client.get(self.url)
        self.assertEqual(200, r.status_code)
        links = pq(r.content)(f"ul.users.{section} .user-name")
        return [pq(el).attr("href").rstrip("/").rsplit("/", 1)[-1] for el in links]

    def test_members_with_same_displayed_name_sorted_by_username(self):
        self.assertEqual(self._usernames("members"), ["alpha", "mike", "zeta"])

    def test_leaders_with_same_displayed_name_sorted_by_username(self):
        self.assertEqual(self._usernames("leaders"), ["alpha", "mike", "zeta"])


class GroupTicketsViewTests(TestCase):
    """Tests for the groups.tickets view."""

    def setUp(self):
        self.SupportTicket = SupportTicket
        product = ProductFactory()

        root_group = Group.objects.create(name="firefox-enterprise")
        self.root = GroupProfile.objects.add_root(
            create_kwargs={
                "group": root_group,
                "slug": "firefox-enterprise",
                "visibility": GroupProfile.Visibility.PRIVATE,
            }
        )
        self.c1_group = Group.objects.create(name="company1")
        self.c1 = GroupProfile.objects.add_child(
            self.root, create_kwargs={"group": self.c1_group, "slug": "company1"}
        )

        self.c2_group = Group.objects.create(name="company2")
        self.c2 = GroupProfile.objects.add_child(
            self.root, create_kwargs={"group": self.c2_group, "slug": "company2"}
        )

        self.member = UserFactory(username="member")
        self.member.groups.add(self.c1_group)
        self.outsider = UserFactory(username="outsider")
        self.outsider.groups.add(self.c2_group)

        self.open_ticket = SupportTicketFactory(
            user=self.member,
            product=product,
            org_group=self.c1,
            zd_status=SupportTicket.ZD_STATUS_OPEN,
        )
        self.solved_ticket = SupportTicketFactory(
            user=self.member,
            product=product,
            org_group=self.c1,
            zd_status=SupportTicket.ZD_STATUS_SOLVED,
        )

    def test_only_enterprise_groups_have_ticket_lists_regardless_of_coverage(self):
        """company2 has no contract; a department lists only the tickets it owns."""
        root_member = UserFactory()
        root_member.groups.add(self.root.group)
        foreign_group = DepartmentFactory(company=GroupProfileFactory())
        foreign_member = UserFactory()
        foreign_member.groups.add(foreign_group.group)
        department = DepartmentFactory(company=self.c1)
        department_member = UserFactory()
        department_member.groups.add(department.group)
        department_ticket = SupportTicketFactory(
            user=department_member, org_group=department, zd_status=SupportTicket.ZD_STATUS_OPEN
        )
        for profile, user, status_code in (
            (self.root, root_member, 404),
            (foreign_group, foreign_member, 404),
            (self.c2, self.outsider, 200),
            (department, department_member, 200),
        ):
            with self.subTest(group=profile.slug):
                self.client.force_login(user)
                response = self.client.get(reverse("groups.tickets", args=[profile.slug]))
                self.assertEqual(response.status_code, status_code)

        self.assertContains(response, department_ticket.subject)
        self.assertNotContains(response, self.open_ticket.subject)

    def test_outsider_cannot_reach_private_group(self):
        """Private + isolated group is invisible to non-members; 404 from visibility gate."""
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("groups.tickets", args=[self.c1.slug]))
        self.assertEqual(response.status_code, 404)

    def test_member_sees_active_tickets_by_default(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("groups.tickets", args=[self.c1.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.open_ticket.subject)
        self.assertNotContains(response, self.solved_ticket.subject)

    def test_status_filter_all(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("groups.tickets", args=[self.c1.slug]) + "?status=all")
        self.assertContains(response, self.open_ticket.subject)
        self.assertContains(response, self.solved_ticket.subject)

    def test_status_filter_solved(self):
        self.client.force_login(self.member)
        response = self.client.get(
            reverse("groups.tickets", args=[self.c1.slug]) + "?status=solved"
        )
        self.assertContains(response, self.solved_ticket.subject)
        self.assertNotContains(response, self.open_ticket.subject)

    def test_only_chats_are_badged_as_live_chats(self):
        chat = SupportTicketFactory(
            user=self.member,
            product=self.open_ticket.product,
            org_group=self.c1,
            zd_status=SupportTicket.ZD_STATUS_OPEN,
            zd_channel=SupportTicket.ZD_CHANNEL_MESSAGING,
        )
        self.client.force_login(self.member)
        response = self.client.get(reverse("groups.tickets", args=[self.c1.slug]))

        rows = pq(response.content)(".group-tickets--table tbody tr")
        badged = [
            pq(row)(".group-tickets--cell-subject a").text()
            for row in rows
            if pq(row)(".my-questions--channel-badge--live-chat")
        ]
        self.assertEqual([chat.subject], badged)

    def test_deleted_ticket_only_under_all(self):
        """A ticket deleted in Zendesk is excluded from active/solved but shown under all."""
        deleted = SupportTicketFactory(
            user=self.member,
            product=self.open_ticket.product,
            org_group=self.c1,
            zd_status=SupportTicket.ZD_STATUS_OPEN,
            zd_deleted_at=timezone.now(),
        )
        self.client.force_login(self.member)
        url = reverse("groups.tickets", args=[self.c1.slug])

        self.assertNotContains(self.client.get(url), deleted.subject)
        self.assertNotContains(self.client.get(url + "?status=solved"), deleted.subject)
        all_response = self.client.get(url + "?status=all")
        self.assertContains(all_response, deleted.subject)
        # The deleted ticket renders with the shared "Inactive" status pill.
        self.assertContains(all_response, "Inactive")

    def test_ticket_of_a_deleted_user_renders_without_links(self):
        leaver = UserFactory()
        orphan = SupportTicketFactory(
            user=leaver,
            product=self.open_ticket.product,
            org_group=self.c1,
            zd_status=SupportTicket.ZD_STATUS_OPEN,
        )
        leaver.delete()

        self.client.force_login(self.member)
        response = self.client.get(reverse("groups.tickets", args=[self.c1.slug]))

        self.assertEqual(response.status_code, 200)
        row = pq(
            next(
                tr
                for tr in pq(response.content)(".group-tickets--table tbody tr")
                if orphan.subject in pq(tr).text()
            )
        )
        self.assertEqual(row(".group-tickets--cell-subject").text(), orphan.subject)
        self.assertFalse(row(".group-tickets--cell-subject a"))
        self.assertEqual(row(".group-tickets--cell-submitter").text(), "deleted user")
        self.assertFalse(row(".group-tickets--cell-submitter a"))

    def test_htmx_request_returns_fragment(self):
        self.client.force_login(self.member)
        response = self.client.get(
            reverse("groups.tickets", args=[self.c1.slug]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"<html", response.content)
        self.assertIn(b'id="tickets-content"', response.content)

    def test_breadcrumb_shows_ancestor_chain(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("groups.tickets", args=[self.c1.slug]))
        self.assertEqual(response.status_code, 200)
        crumbs = pq(response.content)("#main-breadcrumbs a")
        hrefs = [a.attrib["href"] for a in crumbs]
        self.assertIn(reverse("groups.list"), hrefs)
        self.assertIn(reverse("groups.profile", args=[self.root.slug]), hrefs)
        self.assertIn(reverse("groups.profile", args=[self.c1.slug]), hrefs)
        self.assertContains(response, "Tickets")


class CompanySupportSectionTests(TestCase):
    """The company page's Your support section, department links, and My support."""

    def setUp(self):
        today = timezone.localdate()
        self.company = EnterpriseCompanyFactory()
        self.root = GroupProfile.objects.get_parent(self.company)
        self.root.update_visibility(GroupProfile.Visibility.MODERATED)
        self.department = DepartmentFactory(company=self.company)
        self.auditors = GroupFactory()
        self.company.visible_to_groups.add(self.auditors)

        self.thunderbird = ProductFactory(title="Thunderbird")
        self.vpn = ProductFactory(title="VPN")
        ProductSupportConfigFactory(
            product=self.vpn, zendesk_config=ZendeskConfigFactory(), subscription_only=True
        )
        contract = SupportContractFactory(
            company=self.company,
            starts_on=today - timedelta(days=1),
            ends_on=today + timedelta(days=1),
        )
        for product in (self.thunderbird, self.vpn):
            SupportCoverageFactory(contract=contract, product=product)
        self.expired_company = EnterpriseCompanyFactory()
        SupportCoverageFactory(
            product=self.vpn,
            contract__company=self.expired_company,
            contract__starts_on=today - timedelta(days=60),
            contract__ends_on=today - timedelta(days=1),
        )

    def user(self, *profiles, subscribed=False, **kwargs):
        user = UserFactory(**kwargs)
        user.groups.add(*(profile.group for profile in profiles))
        if subscribed:
            user.profile.products.add(self.vpn)
        return user

    def leader(self, profile):
        user = UserFactory()
        profile.leaders.add(user)
        return user

    def get(self, user, url):
        self.client.logout()
        if user.is_authenticated:
            self.client.force_login(user)
        return self.client.get(url)

    def test_section_by_persona(self):
        auditor = UserFactory()
        auditor.groups.add(self.auditors)
        covered = ["Thunderbird", "VPN"]
        for persona, user, company, status_code, expected in (
            ("anonymous", AnonymousUser(), self.company, 404, None),
            ("non-member", self.user(), self.company, 404, None),
            ("individual subscriber", self.user(subscribed=True), self.company, 404, None),
            ("company member", self.user(self.company), self.company, 200, (covered, True)),
            ("department member", self.user(self.department), self.company, 200, (covered, True)),
            (
                "both entitlements",
                self.user(self.company, subscribed=True),
                self.company,
                200,
                (covered, True),
            ),
            ("company leader", self.leader(self.company), self.company, 200, (covered, False)),
            ("root leader", self.leader(self.root), self.company, 200, (covered, False)),
            ("staff", self.user(self.root, is_staff=True), self.company, 200, (covered, False)),
            ("view-only", auditor, self.company, 200, None),
            ("root-only member", self.user(self.root), self.company, 200, None),
            (
                "expired coverage",
                self.user(self.expired_company),
                self.expired_company,
                200,
                ([], False),
            ),
        ):
            with self.subTest(persona=persona):
                response = self.get(user, reverse("groups.profile", args=[company.slug]))
                self.assertEqual(response.status_code, status_code)
                section = pq(response.content)("#your-support")
                if expected is None:
                    self.assertFalse(section)
                    continue
                titles, has_actions = expected
                self.assertCountEqual(
                    [pq(title).text() for title in section(".your-support--title")], titles
                )
                self.assertCountEqual(
                    [link.attrib["href"] for link in section(".your-support--product a")],
                    [
                        reverse("questions.aaq_step3", kwargs={"product_slug": product.slug})
                        for product in (self.thunderbird, self.vpn)
                        if has_actions
                    ],
                )
                self.assertEqual(
                    "This company has no active support coverage." in section.text(), not titles
                )
                tickets_url = reverse("groups.tickets", args=[company.slug])
                self.assertTrue(section(f'a[href="{tickets_url}"]'))

    @override_settings(READ_ONLY=True)
    def test_read_only_mode_lists_coverage_without_submission_actions(self):
        response = self.get(
            self.user(self.company), reverse("groups.profile", args=[self.company.slug])
        )
        section = pq(response.content)("#your-support")
        self.assertCountEqual(
            [pq(title).text() for title in section(".your-support--title")], ["Thunderbird", "VPN"]
        )
        self.assertFalse(section(".your-support--product a"))

    def test_pages_resolve_the_company_once_per_request(self):
        self.client.force_login(self.user(self.company))
        for url in (
            reverse("groups.profile", args=[self.company.slug]),
            reverse("products.product", args=[self.thunderbird.slug]),
        ):
            with self.subTest(url=url):
                with mock.patch.object(
                    GroupProfile.objects,
                    "enterprise_companies",
                    wraps=GroupProfile.objects.enterprise_companies,
                ) as lookup:
                    response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(lookup.call_count, 1)

    def test_department_page_links_to_the_viewers_company_support(self):
        auditor = UserFactory()
        auditor.groups.add(self.auditors)
        company_support = reverse("groups.profile", args=[self.company.slug]) + "#your-support"
        for persona, user, linked in (
            ("department member", self.user(self.department), True),
            ("company member", self.user(self.company), True),
            ("root leader", self.leader(self.root), False),
            ("view-only", auditor, False),
        ):
            with self.subTest(persona=persona):
                response = self.get(user, reverse("groups.profile", args=[self.department.slug]))
                self.assertEqual(response.status_code, 200)
                self.assertFalse(pq(response.content)("#your-support"))
                self.assertEqual(
                    bool(
                        pq(response.content)(f'.group-company-support a[href="{company_support}"]')
                    ),
                    linked,
                )

    def test_tickets_tab_on_company_pages_and_departments_with_history(self):
        member = self.user(self.department)

        def has_tab(profile):
            response = self.get(member, reverse("groups.profile", args=[profile.slug]))
            tickets_url = reverse("groups.tickets", args=[profile.slug])
            return bool(pq(response.content)(f'.tabs a[href="{tickets_url}"]'))

        self.assertTrue(has_tab(self.company))
        self.assertFalse(has_tab(self.department))
        SupportTicketFactory(user=member, org_group=self.department)
        self.assertTrue(has_tab(self.department))

    def test_my_support_links_to_the_users_company_regardless_of_coverage(self):
        for persona, user, company in (
            ("company member", self.user(self.company), self.company),
            ("department member", self.user(self.department), self.company),
            ("member without coverage", self.user(self.expired_company), self.expired_company),
            ("root-only member", self.user(self.root), None),
            ("company leader", self.leader(self.company), None),
            ("anonymous", AnonymousUser(), None),
        ):
            with self.subTest(persona=persona):
                response = self.get(user, reverse("products"))
                links = pq(response.content)('#mzp-c-menu-panel-profile a[href$="#your-support"]')
                self.assertEqual(
                    [link.attrib["href"] for link in links],
                    (
                        [reverse("groups.profile", args=[company.slug]) + "#your-support"]
                        if company
                        else []
                    ),
                )
