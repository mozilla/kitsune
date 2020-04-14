from kitsune.users.tasks import process_unprocessed_account_events
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import AccountEventFactory
from kitsune.users.models import AccountEvent
from nose.tools import eq_


class AccountEventsTasksTestCase(TestCase):
    def test_processes_unprocessed(self):
        event_1 = AccountEventFactory(
            status=AccountEvent.UNPROCESSED,
            event_type=AccountEvent.DELETE_USER
        )
        event_2 = AccountEventFactory(
            status=AccountEvent.UNPROCESSED,
            event_type=AccountEvent.DELETE_USER
        )

        process_unprocessed_account_events()
        event_1.refresh_from_db()
        event_2.refresh_from_db()

        eq_(event_1.status, AccountEvent.PROCESSED)
        eq_(event_2.status, AccountEvent.PROCESSED)
