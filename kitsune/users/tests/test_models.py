import logging

from nose.tools import eq_

from kitsune.sumo.tests import TestCase
from kitsune.users.forms import SettingsForm
from kitsune.users.models import Setting
from kitsune.users.tests import UserFactory

log = logging.getLogger("k.users")


class UserSettingsTests(TestCase):
    def setUp(self):
        self.u = UserFactory()

    def test_non_existant_setting(self):
        form = SettingsForm()
        bad_setting = "doesnt_exist"
        assert bad_setting not in list(form.fields.keys())
        with self.assertRaises(KeyError):
            Setting.get_for_user(self.u, bad_setting)

    def test_default_values(self):
        eq_(0, Setting.objects.count())
        keys = list(SettingsForm.base_fields.keys())
        for setting in keys:
            SettingsForm.base_fields[setting]
            eq_(False, Setting.get_for_user(self.u, setting))
