import logging

from kitsune.sumo.tests import TestCase
from kitsune.tidings.models import Watch
from kitsune.tidings.tests import WatchFactory
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
        self.assertEqual(0, Setting.objects.count())
        keys = list(SettingsForm.base_fields.keys())
        for setting in keys:
            SettingsForm.base_fields[setting]
            self.assertEqual(False, Setting.get_for_user(self.u, setting))


class UserDeactivationTests(TestCase):
    def setUp(self):
        self.u = UserFactory()

    def test_deactivate_user_clears_watches(self):
        WatchFactory(user=self.u)
        assert Watch.objects.filter(user=self.u).exists()

        self.u.is_active = False
        self.u.save()
        assert not Watch.objects.filter(user=self.u).exists()
