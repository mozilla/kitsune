import logging

from kitsune.sumo.tests import TestCase
from kitsune.users.forms import SettingsForm
from kitsune.users.models import AccountEvent, Setting, User
from kitsune.users.tests import AccountEventFactory, UserFactory, ProfileFactory
from nose.tools import eq_
import json

log = logging.getLogger('k.users')


class UserSettingsTests(TestCase):

    def setUp(self):
        self.u = UserFactory()

    def test_non_existant_setting(self):
        form = SettingsForm()
        bad_setting = 'doesnt_exist'
        assert bad_setting not in form.fields.keys()
        with self.assertRaises(KeyError):
            Setting.get_for_user(self.u, bad_setting)

    def test_default_values(self):
        eq_(0, Setting.objects.count())
        keys = SettingsForm.base_fields.keys()
        for setting in keys:
            field = SettingsForm.base_fields[setting]
            eq_(field.initial, Setting.get_for_user(self.u, setting))


class AccountEventTests(TestCase):

    def test_process_delete_user(self):
        profile = ProfileFactory()
        account_event = AccountEventFactory(
            events=json.dumps({
                "https://schemas.accounts.firefox.com/event/delete-user": {}
            }),
            event_type=AccountEvent.DELETE_USER,
            status=AccountEvent.UNPROCESSED,
            profile=profile
        )

        assert User.objects.filter(id=profile.user_id).exists()

        account_event.process()
        account_event.refresh_from_db()

        assert not User.objects.filter(id=profile.user_id).exists()
        eq_(account_event.status, AccountEvent.PROCESSED)

    def test_process_unimplemented(self):
        profile = ProfileFactory()
        account_event = AccountEventFactory(
            events=json.dumps({
                "foobar": {}
            }),
            status=AccountEvent.UNPROCESSED,
            profile=profile
        )

        account_event.process()
        account_event.refresh_from_db()

        eq_(account_event.status, AccountEvent.UNIMPLEMENTED)

    def test_process_error(self):
        account_event = AccountEventFactory(
            events=json.dumps({
                "https://schemas.accounts.firefox.com/event/delete-user": {}
            }),
            event_type=AccountEvent.DELETE_USER,
            status=AccountEvent.UNPROCESSED,
            profile=None
        )

        account_event.process()
        account_event.refresh_from_db()

        eq_(account_event.status, AccountEvent.ERRORED)
        assert account_event.error.find("Traceback") > -1

    def test_process_processed(self):
        account_event = AccountEventFactory(
            event_type=AccountEvent.DELETE_USER,
            status=AccountEvent.PROCESSED
        )

        last_modified = account_event.last_modified

        account_event.process()

        eq_(account_event.last_modified, last_modified)
