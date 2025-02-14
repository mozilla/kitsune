import json
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User

from kitsune.messages.utils import send_message
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.models import AccountEvent
from kitsune.users.tasks import (
    process_event_delete_user,
    process_event_password_change,
    process_event_subscription_state_change,
)
from kitsune.users.tests import AccountEventFactory, GroupFactory, ProfileFactory, UserFactory


class AccountEventsTasksTestCase(TestCase):
    def setUp(self):
        User.objects.get_or_create(username=settings.SUMO_BOT_USERNAME)
        self.content_group = GroupFactory(name=settings.SUMO_CONTENT_GROUP)
        self.group_user1 = UserFactory()
        self.group_user2 = UserFactory()
        self.content_group.user_set.add(self.group_user1, self.group_user2)

    def test_process_delete_user(self):
        profile = ProfileFactory()
        account_event = AccountEventFactory(
            body=json.dumps({}),
            event_type=AccountEvent.DELETE_USER,
            status=AccountEvent.UNPROCESSED,
            profile=profile,
        )
        user = profile.user
        user.username = "ringo"
        user.email = "ringo@beatles.com"
        user.save()
        user.groups.add(GroupFactory())
        # Populate inboxes and outboxes with messages between the user and other users.
        other_users = UserFactory.create_batch(2)
        for sender in other_users:
            send_message({"users": [user]}, text="foo", sender=sender)
        send_message({"users": other_users}, text="bar", sender=user)

        # Confirm the expected initial state.
        self.assertTrue(user.is_active)
        self.assertTrue(user.profile.name)
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.outbox.count(), 1)
        self.assertEqual(user.inbox.count(), len(other_users))
        for other_user in other_users:
            self.assertEqual(other_user.inbox.count(), 1)
            self.assertEqual(other_user.outbox.count(), 1)

        process_event_delete_user(account_event.id)

        with self.assertRaises(User.DoesNotExist):
            user.refresh_from_db()
        account_event.refresh_from_db()

        for other_user in other_users:
            self.assertEqual(other_user.inbox.count(), 1)
            self.assertEqual(other_user.outbox.count(), 1)

        self.assertEqual(account_event.status, AccountEvent.PROCESSED)

    def test_process_subscription_state_change(self):
        product_1 = ProductFactory(codename="capability_1")
        product_2 = ProductFactory(codename="capability_2")
        product_3 = ProductFactory(codename="capability_3")
        profile = ProfileFactory()
        profile.products.add(product_3)
        account_event_1 = AccountEventFactory(
            body=json.dumps(
                {
                    "capabilities": ["capability_1", "capability_2"],
                    "isActive": True,
                    "changeTime": 1,
                }
            ),
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile,
        )

        process_event_subscription_state_change(account_event_1.id)
        account_event_1.refresh_from_db()

        self.assertCountEqual(profile.products.all(), [product_1, product_2, product_3])
        self.assertEqual(account_event_1.status, AccountEvent.PROCESSED)

        account_event_2 = AccountEventFactory(
            body=json.dumps(
                {
                    "capabilities": ["capability_1", "capability_2"],
                    "isActive": False,
                    "changeTime": 2,
                }
            ),
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile,
        )

        process_event_subscription_state_change(account_event_2.id)
        account_event_2.refresh_from_db()

        self.assertCountEqual(profile.products.all(), [product_3])
        self.assertEqual(account_event_2.status, AccountEvent.PROCESSED)

    def test_process_subscription_state_change_out_of_order(self):
        profile = ProfileFactory()
        account_event_1 = AccountEventFactory(
            body=json.dumps({"capabilities": ["capability_1"], "isActive": True, "changeTime": 1}),
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile,
        )

        process_event_subscription_state_change(account_event_1.id)
        account_event_1.refresh_from_db()
        self.assertEqual(account_event_1.status, AccountEvent.PROCESSED)

        account_event_2 = AccountEventFactory(
            body=json.dumps({"capabilities": ["capability_1"], "isActive": True, "changeTime": 3}),
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile,
        )

        process_event_subscription_state_change(account_event_2.id)
        account_event_2.refresh_from_db()
        self.assertEqual(account_event_2.status, AccountEvent.PROCESSED)

        account_event_3 = AccountEventFactory(
            body=json.dumps(
                {"capabilities": ["capability_1"], "isActive": False, "changeTime": 2}
            ),
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile,
        )

        process_event_subscription_state_change(account_event_3.id)
        account_event_3.refresh_from_db()
        self.assertEqual(account_event_3.status, AccountEvent.IGNORED)

    def test_process_password_change(self):
        profile = ProfileFactory()
        account_event_1 = AccountEventFactory(
            body=json.dumps({"changeTime": 2000}),
            event_type=AccountEvent.PASSWORD_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile,
        )

        process_event_password_change(account_event_1.id)

        profile.refresh_from_db()
        account_event_1.refresh_from_db()

        self.assertEqual(profile.fxa_password_change, datetime.utcfromtimestamp(2))
        self.assertEqual(account_event_1.status, AccountEvent.PROCESSED)

        account_event_2 = AccountEventFactory(
            body=json.dumps({"changeTime": 1000}),
            event_type=AccountEvent.PASSWORD_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile,
        )

        process_event_password_change(account_event_2.id)

        profile.refresh_from_db()
        account_event_2.refresh_from_db()

        self.assertEqual(profile.fxa_password_change, datetime.utcfromtimestamp(2))
        self.assertEqual(account_event_2.status, AccountEvent.IGNORED)
