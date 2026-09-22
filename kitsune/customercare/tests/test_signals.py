from unittest.mock import Mock, patch

from django.contrib.auth.models import Group, User

from kitsune.customercare.tasks import notify_agents_if_chat_revoked
from kitsune.groups.models import GroupProfile
from kitsune.products.models import SupportOrganization
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    ZendeskConfigFactory,
)
from kitsune.sumo.tests import TestCase
from kitsune.users.monkeypatch import _deactivate_users
from kitsune.users.tests import UserFactory
from kitsune.users.utils import anonymize_user, delete_user_pipeline


@patch("kitsune.customercare.tasks.notify_agents_of_revoked_chat_access.delay")
class NotifyAgentsIfChatRevokedTests(TestCase):
    def test_queues_the_task_once_the_change_is_saved(self, delay):
        user = UserFactory(profile__fxa_uid="abc123")

        with self.captureOnCommitCallbacks() as callbacks:
            notify_agents_if_chat_revoked(user)
            delay.assert_not_called()

        callbacks[0]()
        delay.assert_called_once_with("abc123", user.id, None)

    def test_passes_along_products_that_just_stopped_offering_chat(self, delay):
        user = UserFactory(profile__fxa_uid="abc123")

        with self.captureOnCommitCallbacks(execute=True):
            notify_agents_if_chat_revoked(user, product_ids=[7])

        delay.assert_called_once_with("abc123", user.id, [7])

    def test_reads_the_fxa_uid_before_anonymizing_replaces_it(self, delay):
        user = UserFactory(profile__fxa_uid="abc123")

        with self.captureOnCommitCallbacks(execute=True):
            notify_agents_if_chat_revoked(user)
            user.profile.fxa_uid = "replaced"
            user.profile.save()

        delay.assert_called_once_with("abc123", user.id, None)

    def test_a_user_without_an_fxa_uid_is_skipped(self, delay):
        user = UserFactory(profile__fxa_uid="")

        with self.captureOnCommitCallbacks(execute=True):
            notify_agents_if_chat_revoked(user)

        delay.assert_not_called()


@patch("kitsune.customercare.signals.notify_agents_if_chat_revoked")
class RevokedChatSignalTests(TestCase):
    def setUp(self):
        self.product = ProductFactory()
        config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=ZendeskConfigFactory()
        )
        root = GroupProfile.add_root(group=Group.objects.create(name="chat"), slug="chat")
        company = root.add_child(group=Group.objects.create(name="company"), slug="company")
        self.org = SupportOrganizationFactory(
            config=config, group=company.group, include_live_chat=True
        )
        # Membership of a subgroup counts for the organization above it.
        self.team = company.add_child(group=Group.objects.create(name="team"), slug="team").group
        self.unrelated = Group.objects.create(name="unrelated")

        self.user = UserFactory(profile__fxa_uid="abc123")
        self.user.groups.add(self.team, self.unrelated)
        self.bystander = UserFactory()
        self.bystander.groups.add(self.unrelated)

    def notified(self, notify):
        return {c.args[0] for c in notify.call_args_list}

    def is_active_in_db(self, notify):
        """Record whether the database has the user as active each time we notify.

        A test runs inside one transaction, so the database already shows a change
        made earlier in the test, even though it isn't committed. Seeing the old value
        means we notified before the change was saved, so the task would read stale data.
        """
        seen = []
        notify.side_effect = lambda user: seen.append(User.objects.get(pk=user.pk).is_active)
        return seen

    def test_deleting_a_user_notifies_before_their_fxa_uid_is_gone(self, notify):
        seen = []
        notify.side_effect = lambda user: seen.append(user.profile.fxa_uid)

        delete_user_pipeline(self.user)

        self.assertEqual(seen[0], "abc123")

    def test_anonymizing_a_user_notifies_after_deactivating_but_before_the_fxa_uid_changes(
        self, notify
    ):
        seen = []
        notify.side_effect = lambda user: seen.append(
            (user.profile.fxa_uid, User.objects.get(pk=user.pk).is_active)
        )

        anonymize_user(self.user)

        self.assertEqual(seen[0], ("abc123", False))

    def test_deleting_or_deactivating_a_user_outside_any_chat_org_does_not(self, notify):
        self.bystander.is_active = False
        self.bystander.save()
        delete_user_pipeline(self.bystander)

        notify.assert_not_called()

    def test_deactivating_a_user_notifies_after_the_save(self, notify):
        active = self.is_active_in_db(notify)

        self.user.is_active = False
        self.user.save()

        self.assertEqual(self.notified(notify), {self.user})
        self.assertEqual(active, [False])

    def test_saving_an_already_inactive_user_does_not(self, notify):
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        self.user.refresh_from_db()

        self.user.save()

        notify.assert_not_called()

    def test_the_admins_bulk_deactivation_notifies_after_the_save(self, notify):
        active = self.is_active_in_db(notify)

        _deactivate_users(Mock(), Mock(), User.objects.filter(pk=self.user.pk))

        self.assertEqual(self.notified(notify), {self.user})
        self.assertEqual(active, [False])

    def test_removal_from_a_chat_group_notifies_from_either_side(self, notify):
        self.user.groups.remove(self.team)
        self.assertEqual(self.notified(notify), {self.user})

        notify.reset_mock()
        self.user.groups.add(self.team)
        self.team.user_set.remove(self.user)
        self.assertEqual(self.notified(notify), {self.user})

    def test_clearing_groups_notifies_from_either_side(self, notify):
        self.user.groups.clear()
        self.assertEqual(self.notified(notify), {self.user})

        notify.reset_mock()
        self.user.groups.add(self.team)
        self.team.user_set.clear()
        self.assertEqual(self.notified(notify), {self.user})

    def test_removal_from_an_unrelated_group_does_not(self, notify):
        self.user.groups.remove(self.unrelated)
        self.unrelated.user_set.clear()

        notify.assert_not_called()

    def test_deleting_a_chat_subgroup_notifies_its_members(self, notify):
        self.team.delete()

        self.assertEqual(self.notified(notify), {self.user})

    def test_deleting_an_unrelated_group_does_not(self, notify):
        self.unrelated.delete()

        notify.assert_not_called()

    def test_switching_chat_off_for_an_organization_notifies_its_members_after_the_save(
        self, notify
    ):
        has_chat = []
        notify.side_effect = lambda user, product_ids: has_chat.append(
            SupportOrganization.objects.get(pk=self.org.pk).include_live_chat
        )

        self.org.include_live_chat = False
        self.org.save()

        self.assertEqual(self.notified(notify), {self.user})
        self.assertEqual(has_chat, [False])
        # The product may have no live-chat organization left, so it's named.
        self.assertEqual(notify.call_args.kwargs["product_ids"], [self.product.pk])

    def test_saving_an_organization_that_keeps_chat_does_not(self, notify):
        self.org.save()

        notify.assert_not_called()

    def test_deleting_an_organization_notifies_its_members(self, notify):
        self.org.delete()

        self.assertEqual(self.notified(notify), {self.user})
        self.assertEqual(notify.call_args.kwargs["product_ids"], [self.product.pk])
