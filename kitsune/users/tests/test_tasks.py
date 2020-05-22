import json
from datetime import datetime
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tasks import (
    process_event_delete_user,
    process_event_subscription_state_change,
    process_event_password_change
)
from kitsune.users.tests import AccountEventFactory, ProfileFactory
from kitsune.users.models import AccountEvent
from nose.tools import eq_


class AccountEventsTasksTestCase(TestCase):

    def test_process_delete_user(self):
        profile = ProfileFactory()
        account_event = AccountEventFactory(
            body=json.dumps({}),
            event_type=AccountEvent.DELETE_USER,
            status=AccountEvent.UNPROCESSED,
            profile=profile
        )

        assert profile.user.is_active

        process_event_delete_user(account_event.id)

        profile.user.refresh_from_db()
        account_event.refresh_from_db()

        assert not profile.user.is_active
        eq_(account_event.status, AccountEvent.PROCESSED)

    def test_process_subscription_state_change(self):
        product_1 = ProductFactory(codename="capability_1")
        product_2 = ProductFactory(codename="capability_2")
        product_3 = ProductFactory(codename="capability_3")
        profile = ProfileFactory()
        profile.products.add(product_3)
        account_event_1 = AccountEventFactory(
            body=json.dumps({
                "capabilities": ["capability_1", "capability_2"],
                "isActive": True,
                "changeTime": 1
            }),
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile
        )

        process_event_subscription_state_change(account_event_1.id)
        account_event_1.refresh_from_db()

        self.assertItemsEqual(profile.products.all(), [product_1, product_2, product_3])
        eq_(account_event_1.status, AccountEvent.PROCESSED)

        account_event_2 = AccountEventFactory(
            body=json.dumps({
                "capabilities": ["capability_1", "capability_2"],
                "isActive": False,
                "changeTime": 2
            }),
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile
        )

        process_event_subscription_state_change(account_event_2.id)
        account_event_2.refresh_from_db()

        self.assertItemsEqual(profile.products.all(), [product_3])
        eq_(account_event_2.status, AccountEvent.PROCESSED)

    def test_process_subscription_state_change_out_of_order(self):
        profile = ProfileFactory()
        account_event_1 = AccountEventFactory(
            body=json.dumps({
                "capabilities": ["capability_1"],
                "isActive": True,
                "changeTime": 1
            }),
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile
        )

        process_event_subscription_state_change(account_event_1.id)
        account_event_1.refresh_from_db()
        eq_(account_event_1.status, AccountEvent.PROCESSED)

        account_event_2 = AccountEventFactory(
            body=json.dumps({
                "capabilities": ["capability_1"],
                "isActive": True,
                "changeTime": 3
            }),
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile
        )

        process_event_subscription_state_change(account_event_2.id)
        account_event_2.refresh_from_db()
        eq_(account_event_2.status, AccountEvent.PROCESSED)

        account_event_3 = AccountEventFactory(
            body=json.dumps({
                "capabilities": ["capability_1"],
                "isActive": False,
                "changeTime": 2
            }),
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile
        )

        process_event_subscription_state_change(account_event_3.id)
        account_event_3.refresh_from_db()
        eq_(account_event_3.status, AccountEvent.IGNORED)

    def test_process_password_change(self):
        profile = ProfileFactory()
        account_event_1 = AccountEventFactory(
            body=json.dumps({
                "changeTime": 2000
            }),
            event_type=AccountEvent.PASSWORD_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile
        )

        process_event_password_change(account_event_1.id)

        profile.refresh_from_db()
        account_event_1.refresh_from_db()

        eq_(profile.fxa_password_change, datetime.utcfromtimestamp(2))
        eq_(account_event_1.status, AccountEvent.PROCESSED)

        account_event_2 = AccountEventFactory(
            body=json.dumps({
                "changeTime": 1000
            }),
            event_type=AccountEvent.PASSWORD_CHANGE,
            status=AccountEvent.UNPROCESSED,
            profile=profile
        )

        process_event_password_change(account_event_2.id)

        profile.refresh_from_db()
        account_event_2.refresh_from_db()

        eq_(profile.fxa_password_change, datetime.utcfromtimestamp(2))
        eq_(account_event_2.status, AccountEvent.IGNORED)
