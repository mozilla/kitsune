from unittest.mock import Mock, patch

from django.contrib.auth.models import Group, User

from kitsune.customercare.tasks import revoke_chat_tickets
from kitsune.groups.models import GroupProfile
from kitsune.products.models import ProductSupportConfig, SupportOrganization
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.tests import AAQConfigFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.monkeypatch import _deactivate_users
from kitsune.users.tests import UserFactory
from kitsune.users.utils import anonymize_user, delete_user_pipeline


@patch("kitsune.customercare.tasks.tag_revoked_chat_tickets.delay")
class TagChatTicketsIfRevokedTests(TestCase):
    def setUp(self):
        # Saving a user with a zendesk_id would otherwise call Zendesk.
        self.enterContext(patch("kitsune.customercare.signals.update_zendesk_user"))

    def test_queues_the_task_after_the_commit_with_the_zendesk_id_read_now(self, delay):
        user = UserFactory(profile__zendesk_id="789")

        with self.captureOnCommitCallbacks(execute=True):
            revoke_chat_tickets(user)
            # Deleting the user erases their zendesk_id before the commit.
            user.delete()
            delay.assert_not_called()

        delay.assert_called_once_with("789")

    def test_a_user_without_a_zendesk_id_is_skipped(self, delay):
        user = UserFactory(profile__zendesk_id="")

        with self.captureOnCommitCallbacks(execute=True):
            revoke_chat_tickets(user)

        delay.assert_not_called()


@patch("kitsune.customercare.signals.revoke_chat_tickets")
class RevokedChatSignalTests(TestCase):
    def setUp(self):
        # Saving a user with a zendesk_id would otherwise call Zendesk.
        self.enterContext(patch("kitsune.customercare.signals.update_zendesk_user"))
        self.product = ProductFactory()
        self.config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=ZendeskConfigFactory()
        )
        root = GroupProfile.add_root(group=Group.objects.create(name="chat"), slug="chat")
        company = root.add_child(group=Group.objects.create(name="company"), slug="company")
        self.org = SupportOrganizationFactory(
            config=self.config, group=company.group, include_live_chat=True
        )
        # Membership of a subgroup counts for the organization above it.
        self.team = company.add_child(group=Group.objects.create(name="team"), slug="team").group
        self.unrelated = Group.objects.create(name="unrelated")

        self.user = UserFactory(profile__zendesk_id="789")
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

    def test_deleting_a_user_tags_before_their_zendesk_id_is_gone(self, notify):
        seen = []
        notify.side_effect = lambda user: seen.append(user.profile.zendesk_id)

        delete_user_pipeline(self.user)

        self.assertEqual(seen[0], "789")

    def test_anonymizing_a_user_tags_after_deactivating_with_the_zendesk_id_intact(self, notify):
        seen = []
        notify.side_effect = lambda user: seen.append(
            (user.profile.zendesk_id, User.objects.get(pk=user.pk).is_active)
        )

        anonymize_user(self.user)

        self.assertEqual(seen[0], ("789", False))

    def test_deleting_or_deactivating_a_user_outside_any_chat_org_does_not(self, notify):
        self.bystander.is_active = False
        self.bystander.save()
        delete_user_pipeline(self.bystander)

        notify.assert_not_called()

    def test_deactivating_a_user_tags_after_the_save(self, notify):
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

    def test_the_admins_bulk_deactivation_tags_after_the_save(self, notify):
        active = self.is_active_in_db(notify)

        _deactivate_users(Mock(), Mock(), User.objects.filter(pk=self.user.pk))

        self.assertEqual(self.notified(notify), {self.user})
        self.assertEqual(active, [False])

    def test_removal_from_a_chat_group_tags_from_either_side(self, notify):
        self.user.groups.remove(self.team)
        self.assertEqual(self.notified(notify), {self.user})

        notify.reset_mock()
        self.user.groups.add(self.team)
        self.team.user_set.remove(self.user)
        self.assertEqual(self.notified(notify), {self.user})

    def test_clearing_groups_tags_from_either_side(self, notify):
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

    def test_deleting_a_chat_subgroup_tags_its_members(self, notify):
        self.team.delete()

        self.assertEqual(self.notified(notify), {self.user})

    def test_deleting_an_unrelated_group_does_not(self, notify):
        self.unrelated.delete()

        notify.assert_not_called()

    def test_switching_chat_off_for_an_organization_tags_its_members_after_the_save(self, notify):
        has_chat = []
        notify.side_effect = lambda user: has_chat.append(
            SupportOrganization.objects.get(pk=self.org.pk).include_live_chat
        )

        self.org.include_live_chat = False
        self.org.save()

        self.assertEqual(self.notified(notify), {self.user})
        self.assertEqual(has_chat, [False])

    def test_saving_an_organization_that_keeps_chat_does_not(self, notify):
        self.org.save()

        notify.assert_not_called()

    def test_deleting_an_organization_tags_its_members(self, notify):
        self.org.delete()

        self.assertEqual(self.notified(notify), {self.user})

    def test_switching_off_a_config_tags_its_organizations_members(self, notify):
        self.config.is_active = False
        self.config.save()

        self.assertEqual(self.notified(notify), {self.user})

    def test_dropping_zendesk_from_a_config_tags_its_organizations_members(self, notify):
        self.config.forum_config = AAQConfigFactory()
        self.config.zendesk_config = None
        self.config.save()

        self.assertEqual(self.notified(notify), {self.user})

    def test_a_config_requiring_a_subscription_tags_its_organizations_members(self, notify):
        self.config.subscription_only = True
        self.config.save()

        self.assertEqual(self.notified(notify), {self.user})

    def test_saving_a_config_that_keeps_chat_does_not(self, notify):
        self.config.save()

        notify.assert_not_called()

    def test_losing_a_subscription_that_chat_does_not_require_does_not(self, notify):
        self.user.profile.products.add(self.product)

        self.user.profile.products.remove(self.product)

        notify.assert_not_called()

    def test_a_login_sync_tags_only_when_the_subscription_is_gone(self, notify):
        ProductSupportConfig.objects.filter(pk=self.config.pk).update(subscription_only=True)
        self.user.profile.products.add(self.product)

        # The login sync sets the products from the Mozilla account's subscriptions.
        self.user.profile.products.set([self.product])
        notify.assert_not_called()

        self.user.profile.products.set([])
        self.assertEqual(self.notified(notify), {self.user})
