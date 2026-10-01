import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.manager import BaseManager
from django.test import override_settings

from kitsune.sumo.tests import TestCase
from kitsune.users.forms import SettingsForm
from kitsune.users.models import Profile, Setting
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


class UserManagerTests(TestCase):
    def test_app_registry_rebuild_preserves_user_creation_and_system_filtering(self):
        regular = UserFactory()
        system = UserFactory(profile__account_type=Profile.AccountType.SYSTEM)
        self.addCleanup(setattr, User, "objects", User.objects)
        self.addCleanup(setattr, User, "all_users", User.all_users)
        self.addCleanup(setattr, BaseManager, "all", BaseManager.all)

        with override_settings(INSTALLED_APPS=settings.INSTALLED_APPS):
            created = UserFactory()

        user_ids = [regular.pk, system.pk, created.pk]
        self.assertQuerySetEqual(
            User.objects.filter(pk__in=user_ids).order_by("pk"), [regular, created]
        )
        self.assertQuerySetEqual(
            User.all_users.filter(pk__in=user_ids).order_by("pk"), [regular, system, created]
        )
