from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from kombu.exceptions import OperationalError
from waffle.testutils import override_switch

from kitsune.customercare.tasks import (
    revoke_chat_tickets,
    revoke_expired_chat,
    tag_revoked_chat_tickets,
)
from kitsune.customercare.zendesk import CHAT_REVOKED_TAG
from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.products.models import Product, SupportContract
from kitsune.products.tests import SupportCoverageFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.monkeypatch import _deactivate_users
from kitsune.users.tests import UserFactory
from kitsune.users.utils import anonymize_user, delete_user_pipeline


@patch("kitsune.customercare.signals.update_zendesk_user.delay")
class ZendeskUserSyncSignalTests(TestCase):
    def test_sync_is_queued_after_commit(self, delay):
        user = UserFactory(profile__zendesk_id="789")
        with self.captureOnCommitCallbacks(execute=True):
            user.profile.name = "Renamed"
            user.profile.save(update_fields=["name"])
            delay.assert_not_called()
        delay.assert_called_once_with(user.pk)


@patch("kitsune.customercare.tasks.tag_revoked_chat_tickets.delay")
class TagChatTicketsIfRevokedTests(TestCase):
    def setUp(self):
        # Saving a user with a zendesk_id would otherwise call Zendesk.
        self.enterContext(patch("kitsune.customercare.signals.update_zendesk_user"))
        self.enterContext(patch("kitsune.groups.tasks.remove_stale_zendesk_memberships.delay"))

    def test_queues_the_task_after_the_commit_with_the_zendesk_id_read_now(self, delay):
        user = UserFactory(profile__zendesk_id="789")
        now = timezone.now()

        with (
            patch("kitsune.customercare.tasks.timezone.now", return_value=now),
            self.captureOnCommitCallbacks(execute=True),
        ):
            revoke_chat_tickets(user)
            # Deleting the user erases their zendesk_id before the commit.
            user.delete()
            delay.assert_not_called()

        delay.assert_called_once_with("789", product_slugs=None, before=now.isoformat())

    def test_a_user_without_a_zendesk_id_is_skipped(self, delay):
        user = UserFactory(profile__zendesk_id="")

        with self.captureOnCommitCallbacks(execute=True):
            revoke_chat_tickets(user)

        delay.assert_not_called()

    def test_publication_failure_does_not_abort_account_deletion(self, delay):
        user = UserFactory(profile__zendesk_id="789")
        user_id = user.pk
        delay.side_effect = OperationalError("broker unavailable")

        with self.captureOnCommitCallbacks(execute=True):
            revoke_chat_tickets(user)
            user.delete()

        self.assertFalse(User.all_users.filter(pk=user_id).exists())


def save(instance, **changes):
    for field, value in changes.items():
        setattr(instance, field, value)
    instance.save()


@patch("kitsune.customercare.tasks.tag_revoked_chat_tickets.delay")
class ChatRevocationTests(TestCase):
    def setUp(self):
        # Saving a user with a zendesk_id would otherwise call Zendesk.
        self.enterContext(patch("kitsune.customercare.signals.update_zendesk_user"))
        self.enterContext(patch("kitsune.groups.tasks.sync_enterprise_zendesk_membership.delay"))
        self.enterContext(patch("kitsune.groups.tasks.remove_stale_zendesk_memberships.delay"))
        self.today = timezone.localdate()
        self.yesterday = self.today - timedelta(days=1)

    def member(self, includes_chat=True, ends_on=None):
        """A department member of a company whose contract runs until `ends_on`."""
        coverage = SupportCoverageFactory(
            includes_chat=includes_chat,
            contract__ends_on=ends_on or self.today + timedelta(days=30),
        )
        department = DepartmentFactory(company=coverage.contract.company)
        user = UserFactory(profile__zendesk_id=str(uuid4()))
        user.groups.add(department.group)
        return SimpleNamespace(
            user=user,
            zendesk_id=user.profile.zendesk_id,
            department=department,
            coverage=coverage,
            contract=coverage.contract,
        )

    def tagged(self, delay, change, member):
        delay.reset_mock()
        with self.captureOnCommitCallbacks(execute=True):
            change(member)
            delay.assert_not_called()
        return {call.args[0] for call in delay.call_args_list}

    def expire(self, member, renewed=False, days_ago=1):
        SupportContract.objects.filter(pk=member.contract.pk).update(
            ends_on=self.today - timedelta(days=days_ago)
        )
        if renewed:
            SupportCoverageFactory(
                product=member.coverage.product,
                includes_chat=True,
                contract__company=member.contract.company,
                contract__starts_on=self.today,
                contract__ends_on=self.today + timedelta(days=30),
            )
        revoke_expired_chat()

    def test_losing_chat_tags_the_members_chats_after_commit(self, delay):
        other_company = EnterpriseCompanyFactory()
        for name, change in (
            ("leaving the company", lambda m: m.user.groups.remove(m.department.group)),
            ("removal by the group", lambda m: m.department.group.user_set.remove(m.user)),
            ("clearing the user's groups", lambda m: m.user.groups.clear()),
            ("clearing the group's members", lambda m: m.department.group.user_set.clear()),
            ("deleting the department", lambda m: m.department.group.delete()),
            (
                "moving the department to another company",
                lambda m: GroupProfile.objects.move(m.department, other_company, "last-child"),
            ),
            ("deactivation", lambda m: save(m.user, is_active=False)),
            (
                "the admin's bulk deactivation",
                lambda m: _deactivate_users(Mock(), Mock(), User.objects.filter(pk=m.user.pk)),
            ),
            ("anonymization", lambda m: anonymize_user(m.user)),
            ("deletion", lambda m: delete_user_pipeline(m.user)),
            (
                "suspending the contract",
                lambda m: save(m.contract, status=SupportContract.Status.SUSPENDED),
            ),
            (
                "cancelling the contract",
                lambda m: save(m.contract, status=SupportContract.Status.CANCELLED),
            ),
            ("ending the contract early", lambda m: save(m.contract, ends_on=self.yesterday)),
            ("turning chat off", lambda m: save(m.coverage, includes_chat=False)),
            ("archiving the product", lambda m: save(m.coverage.product, is_archived=True)),
            ("the contract running out", self.expire),
            ("the contract running out during skipped runs", lambda m: self.expire(m, days_ago=7)),
        ):
            with self.subTest(name), transaction.atomic():
                member = self.member()
                self.assertEqual(self.tagged(delay, change, member), {member.zendesk_id})
                transaction.set_rollback(True)

    def test_users_who_keep_or_never_had_chat_are_not_tagged(self, delay):
        unrelated = GroupProfileFactory()

        def leave(member):
            member.user.groups.remove(member.department.group)

        def leave_unrelated_group(member):
            member.user.groups.add(unrelated.group)
            member.user.groups.remove(unrelated.group)

        def resave_inactive_user(member):
            User.objects.filter(pk=member.user.pk).update(is_active=False)
            member.user.refresh_from_db()
            member.user.save()

        def leave_department_but_stay_in_company(member):
            member.user.groups.add(member.contract.company.group)
            leave(member)

        def delete_one_of_two_departments(member):
            member.user.groups.add(DepartmentFactory(company=member.contract.company).group)
            member.department.group.delete()

        def deactivate_quietly(member):
            User.objects.filter(pk=member.user.pk).update(is_active=False)

        def remove_inactive_member(member):
            deactivate_quietly(member)
            leave(member)

        def suspend_inactive_members_contract(member):
            deactivate_quietly(member)
            save(member.contract, status=SupportContract.Status.SUSPENDED)

        def resave_archived_product(member):
            Product.objects.filter(pk=member.coverage.product_id).update(is_archived=True)
            save(member.coverage.product, is_archived=True)

        for name, member_kwargs, change in (
            ("leaving a company without chat", {"includes_chat": False}, leave),
            (
                "leaving over a week after the contract ended",
                {"ends_on": self.today - timedelta(days=8)},
                leave,
            ),
            ("leaving a group outside the company", {}, leave_unrelated_group),
            (
                "leaving a department while still in the company",
                {},
                leave_department_but_stay_in_company,
            ),
            ("deleting one of two departments", {}, delete_one_of_two_departments),
            ("removing an inactive member", {}, remove_inactive_member),
            ("suspending an inactive member's contract", {}, suspend_inactive_members_contract),
            (
                "deactivating a user without chat",
                {"includes_chat": False},
                lambda m: save(m.user, is_active=False),
            ),
            ("saving an already inactive user", {}, resave_inactive_user),
            (
                "deleting a user without chat",
                {"includes_chat": False},
                lambda m: delete_user_pipeline(m.user),
            ),
            ("saving a contract that keeps chat", {}, lambda m: save(m.contract)),
            ("re-saving an archived product", {}, resave_archived_product),
            (
                "archiving a product without chat",
                {"includes_chat": False},
                lambda m: save(m.coverage.product, is_archived=True),
            ),
            (
                "the contract running out with a renewal",
                {},
                lambda m: self.expire(m, renewed=True),
            ),
            (
                "the daily run on the contract's last day",
                {"ends_on": self.today},
                lambda m: revoke_expired_chat(),
            ),
            (
                "the contract running out over a week ago",
                {},
                lambda m: self.expire(m, days_ago=8),
            ),
        ):
            with self.subTest(name), transaction.atomic():
                member = self.member(**member_kwargs)
                self.assertEqual(self.tagged(delay, change, member), set())
                transaction.set_rollback(True)

    def test_changes_after_expiry_do_not_escape_the_daily_cleanup(self, delay):
        for name, change in (
            ("departure", lambda m: m.user.groups.remove(m.department.group)),
            ("deactivation", lambda m: save(m.user, is_active=False)),
            ("deletion", lambda m: delete_user_pipeline(m.user)),
            ("cancellation", lambda m: save(m.contract, status=SupportContract.Status.CANCELLED)),
            ("chat disabled", lambda m: save(m.coverage, includes_chat=False)),
        ):
            with self.subTest(name), transaction.atomic():
                member = self.member(ends_on=self.yesterday)
                self.assertEqual(self.tagged(delay, change, member), {member.zendesk_id})
                transaction.set_rollback(True)

    @override_switch("zendesk-chat", active=True)
    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_losing_one_products_coverage_keeps_other_product_chats(self, client_class, delay):
        member = self.member()
        other = SupportCoverageFactory(contract=member.contract, includes_chat=True)
        prefix = settings.ZENDESK_CHAT_PRODUCT_TAG_PREFIX
        client = client_class.return_value
        client.get_active_chat_tickets.return_value = [
            Mock(
                id=ticket_id,
                created_at="2020-01-01T00:00:00Z",
                tags=[f"{prefix}{coverage.product.slug}"],
            )
            for ticket_id, coverage in ((1, member.coverage), (2, other))
        ]

        with self.captureOnCommitCallbacks(execute=True):
            save(member.coverage, includes_chat=False)
            delay.assert_not_called()
        tag_revoked_chat_tickets(*delay.call_args.args, **delay.call_args.kwargs)

        client.add_ticket_tags.assert_called_once_with(1, [CHAT_REVOKED_TAG])

    def test_a_rolled_back_change_tags_nothing(self, delay):
        member = self.member()

        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(RuntimeError), transaction.atomic():
                member.user.groups.remove(member.department.group)
                save(member.contract, status=SupportContract.Status.SUSPENDED)
                raise RuntimeError

        delay.assert_not_called()
