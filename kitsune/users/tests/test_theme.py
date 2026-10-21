from contextlib import nullcontext
from unittest import mock

from django.contrib.auth.models import AnonymousUser, User
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils.crypto import constant_time_compare
from pyquery import PyQuery as pq
from waffle.testutils import override_flag

from kitsune.sumo.tests import TestCase
from kitsune.sumo.theme import DARK_MODE_FLAG
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.forms import SettingsForm
from kitsune.users.models import Setting
from kitsune.users.tests import UserFactory
from kitsune.users.theme import (
    THEME_PREFERENCES,
    get_theme_preference,
    set_theme_preference,
    theme_owner_key,
)

NOTIFICATION_SETTINGS = list(SettingsForm.base_fields)
FIELD_RADIOS = 'input[name="theme_preference"]'
FLAG_OFF_STATES = {
    "missing": nullcontext,
    "off": lambda: override_flag(DARK_MODE_FLAG, active=False),
}


def store_raw(user, value):
    Setting.objects.update_or_create(user=user, name="theme_preference", defaults={"value": value})


def stored(user, name="theme_preference"):
    return list(Setting.objects.filter(user=user, name=name).values_list("value", flat=True))


class ThemePreferenceStorageTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_default_is_system_and_reading_creates_no_row(self):
        self.assertEqual("system", get_theme_preference(self.user))
        self.assertFalse(Setting.objects.filter(user=self.user).exists())

    def test_set_keeps_one_row_per_user(self):
        other = UserFactory()
        set_theme_preference(other, "light")

        for preference in THEME_PREFERENCES:
            with self.subTest(preference):
                set_theme_preference(self.user, preference)

                self.assertEqual(preference, get_theme_preference(self.user))
        self.assertEqual(1, len(stored(self.user)))
        self.assertEqual("light", get_theme_preference(other))

    def test_invalid_preference_raises_and_keeps_the_stored_value(self):
        set_theme_preference(self.user, "light")

        for preference in ("", "Dark", "dark\n", "auto", None, 1, ["dark"], b"dark"):
            with self.subTest(preference=preference):
                with self.assertRaises(ValueError):
                    set_theme_preference(self.user, preference)

                self.assertEqual(["light"], stored(self.user))

    def test_corrupt_stored_value_reads_as_the_default(self):
        for value in ("", "neon", "DARK", "dark "):
            with self.subTest(value=value):
                store_raw(self.user, value)

                self.assertEqual("system", get_theme_preference(self.user))

    def test_users_without_a_pk_read_the_default_and_cannot_store_or_own(self):
        for user in (AnonymousUser(), User(username="unsaved")):
            with self.subTest(user=user):
                with self.assertNumQueries(0):
                    self.assertEqual("system", get_theme_preference(user))
                with self.assertRaises(ValueError):
                    set_theme_preference(user, "dark")
                with self.assertRaises(ValueError):
                    theme_owner_key(user)

        self.assertFalse(Setting.objects.filter(name="theme_preference").exists())

    def test_owner_key_is_a_stable_per_account_digest(self):
        key = theme_owner_key(self.user)

        self.assertRegex(key, r"^[0-9a-f]{64}$")
        self.assertEqual(key, theme_owner_key(User.objects.get(pk=self.user.pk)))
        self.assertNotEqual(key, theme_owner_key(UserFactory()))


@override_flag(DARK_MODE_FLAG, active=True)
class ThemePreferenceEndpointTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.url = reverse("users.theme_preference", locale="en-US")

    def post(self, client=None, headers=None, **changes):
        data = {"preference": "dark", "owner": theme_owner_key(self.user), **changes}
        data = {name: value for name, value in data.items() if value is not None}
        return (client or self.client).post(self.url, data, headers=headers)

    def test_requires_a_signed_in_csrf_protected_post(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        anonymous = self.post(Client(), headers={"x-requested-with": "XMLHttpRequest"})
        self.assertEqual(403, anonymous.status_code)
        self.assertEqual(403, self.post(csrf_client).status_code)
        self.assertEqual(405, self.client.get(self.url).status_code)
        self.assertEqual([], stored(self.user))

    def test_valid_save_returns_and_stores_the_preference(self):
        for preference in THEME_PREFERENCES:
            with self.subTest(preference):
                response = self.post(preference=preference)

                self.assertEqual(200, response.status_code)
                self.assertEqual({"preference": preference}, response.json())
                self.assertEqual([preference], stored(self.user))

    def test_unknown_preference_or_missing_owner_gets_400(self):
        set_theme_preference(self.user, "light")
        cases = [{"preference": value} for value in ("", "Dark", "dark ", "x" * 1000, None)]
        cases += [{"owner": value} for value in ("", None)]

        for changes in cases:
            with self.subTest(changes=changes):
                response = self.post(**changes)

                self.assertEqual(400, response.status_code)
                self.assertEqual(["error"], list(response.json()))
                self.assertEqual(["light"], stored(self.user))

    def test_another_accounts_owner_gets_409_and_changes_nothing(self):
        set_theme_preference(self.user, "light")
        stale_tab = UserFactory()
        key = theme_owner_key(self.user)
        owners = (theme_owner_key(stale_tab), key.upper(), key[:-1], "é" * 64, "\u0000" + key)

        for owner in owners:
            # "neon" also shows the owner is checked before the preference.
            for preference in ("dark", "neon"):
                with self.subTest(owner=owner, preference=preference):
                    response = self.post(owner=owner, preference=preference)

                    self.assertEqual(409, response.status_code)
                    self.assertEqual(["error"], list(response.json()))
                    self.assertNotIn("light", response.content.decode())

        self.assertEqual(["light"], stored(self.user))
        self.assertEqual([], stored(stale_tab))

        with mock.patch(
            "kitsune.users.views.constant_time_compare", wraps=constant_time_compare
        ) as compare:
            self.post(owner=owners[0])
        compare.assert_called_once_with(owners[0], key)


class ThemePreferenceEndpointFlagOffTests(TestCase):
    def test_flag_off_gets_404_and_keeps_the_stored_preference(self):
        user = UserFactory()
        set_theme_preference(user, "dark")
        signed_in = Client()
        signed_in.force_login(user)
        url = reverse("users.theme_preference", locale="en-US")
        data = {"preference": "light", "owner": theme_owner_key(user)}

        for flag, flag_state in FLAG_OFF_STATES.items():
            with self.subTest(flag), flag_state():
                self.assertEqual(404, signed_in.post(url, data).status_code)
                self.assertEqual(404, signed_in.get(url).status_code)
                self.assertEqual(404, Client().post(url, data).status_code)

        self.assertEqual(["dark"], stored(user))


@override_flag(DARK_MODE_FLAG, active=True)
class ThemeAttributesTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.client.force_login(self.user)

    def html_attributes(self):
        response = self.client.get(reverse("home"), follow=True)
        self.assertEqual(200, response.status_code)
        return pq(response.content, parser="html")("html")[0].attrib

    def test_signed_in_page_carries_the_preference_owner_and_endpoint(self):
        cases = [(preference, preference) for preference in THEME_PREFERENCES]
        cases.append(('"><script>x</script>', "system"))

        for value, expected in cases:
            with self.subTest(value=value):
                store_raw(self.user, value)

                attributes = self.html_attributes()

                self.assertEqual(expected, attributes["data-theme-preference"])
                self.assertEqual(theme_owner_key(self.user), attributes["data-theme-owner"])
                self.assertEqual("/en-US/users/theme", attributes["data-theme-endpoint"])
                self.assertEqual("en-US", attributes["lang"])

    def test_preference_is_read_once_per_render(self):
        def setting_queries():
            with CaptureQueriesContext(connection) as queries:
                self.html_attributes()
            return sum('"users_setting"' in query["sql"] for query in queries)

        flag_on = setting_queries()
        with override_flag(DARK_MODE_FLAG, active=False):
            flag_off = setting_queries()

        self.assertEqual(flag_off + 1, flag_on)


class SettingsFormThemeFieldTests(TestCase):
    def test_theme_field_exists_only_on_an_enabled_form(self):
        field = SettingsForm(theme_enabled=True).fields["theme_preference"]

        self.assertEqual(list(THEME_PREFERENCES), [value for value, _label in field.choices])
        self.assertEqual("system", field.initial)
        self.assertEqual(NOTIFICATION_SETTINGS, list(SettingsForm().fields))


class SettingsPageTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.url = reverse("users.edit_settings", locale="en-US")

    def get_page(self):
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        return pq(response.content, parser="html")

    def checked(self, doc):
        return [radio.get("value") for radio in doc(f"{FIELD_RADIOS}[checked]")]


class SettingsThemeFlagOffTests(SettingsPageTestCase):
    def test_flag_off_neither_renders_nor_saves_the_field(self):
        set_theme_preference(self.user, "dark")

        for flag, flag_state in FLAG_OFF_STATES.items():
            with self.subTest(flag), flag_state():
                doc = self.get_page()

                self.assertEqual(0, len(doc(FIELD_RADIOS)))
                boxes = doc("#edit-settings form input[type=checkbox]")
                self.assertEqual(NOTIFICATION_SETTINGS, [box.get("name") for box in boxes])
                for value in ("light", "neon"):
                    response = self.client.post(
                        self.url, {"forums_watch_new_thread": "on", "theme_preference": value}
                    )
                    self.assertRedirects(response, self.url, fetch_redirect_response=False)
                self.assertEqual(["dark"], stored(self.user))
                self.assertEqual(["True"], stored(self.user, "forums_watch_new_thread"))


@override_flag(DARK_MODE_FLAG, active=True)
class SettingsThemeFlagOnTests(SettingsPageTestCase):
    def submit_rendered_form(self, doc, **changes):
        """Post what a browser would send for the rendered form, with no JavaScript."""
        data = {}
        for control in doc("#edit-settings form input").items():
            if control.attr("type") in ("checkbox", "radio") and control.attr("checked") is None:
                continue
            data[control.attr("name")] = control.attr("value") or "on"
        data.update(changes)
        return self.client.post(self.url, data)

    def test_page_renders_the_field_after_the_notification_settings(self):
        doc = self.get_page()

        switcher = doc("#edit-settings form .sumo-theme-switcher")
        self.assertEqual(1, len(switcher))
        self.assertIn("is-field", switcher.attr("class").split())
        self.assertNotIn("hidden", switcher[0].attrib)
        self.assertEqual(
            list(THEME_PREFERENCES), [radio.get("value") for radio in switcher.find(FIELD_RADIOS)]
        )
        names = [
            control.get("name")
            for control in doc("#edit-settings form input")
            if control.get("name") != "csrfmiddlewaretoken"
        ]
        self.assertEqual([*NOTIFICATION_SETTINGS, *["theme_preference"] * 3], names)

    def test_page_checks_the_stored_choice_or_the_default(self):
        self.assertEqual(["system"], self.checked(self.get_page()))
        self.assertFalse(Setting.objects.filter(user=self.user).exists())

        # "{[]:1}" would crash the literal_eval the page applies to other settings.
        cases = [(preference, preference) for preference in THEME_PREFERENCES]
        cases += [("neon", "system"), ("DARK", "system"), ("{[]:1}", "system")]
        for value, expected in cases:
            with self.subTest(value=value):
                store_raw(self.user, value)

                self.assertEqual([expected], self.checked(self.get_page()))

    def test_valid_save_stores_the_choice_and_the_notification_settings(self):
        for preference in THEME_PREFERENCES:
            with self.subTest(preference):
                response = self.client.post(
                    self.url, {"forums_watch_after_reply": "on", "theme_preference": preference}
                )

                self.assertRedirects(response, self.url, fetch_redirect_response=False)
                self.assertEqual([preference], stored(self.user))
                self.assertEqual(["True"], stored(self.user, "forums_watch_after_reply"))

    def test_invalid_or_missing_choice_is_a_form_error_and_nothing_is_saved(self):
        set_theme_preference(self.user, "light")

        for value in ("neon", "Dark", "", None):
            with self.subTest(value=value):
                data = {"forums_watch_new_thread": "on"}
                if value is not None:
                    data["theme_preference"] = value

                response = self.client.post(self.url, data)

                self.assertEqual(200, response.status_code)
                doc = pq(response.content, parser="html")
                self.assertEqual(1, len(doc("#edit-settings .form-error")))
                self.assertEqual(3, len(doc(FIELD_RADIOS)))
                self.assertEqual([], self.checked(doc))
                self.assertEqual(["light"], stored(self.user))
                self.assertEqual([], stored(self.user, "forums_watch_new_thread"))

    def test_the_form_works_without_javascript(self):
        set_theme_preference(self.user, "light")
        doc = self.get_page()

        response = self.submit_rendered_form(doc)
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.assertEqual(["light"], stored(self.user))

        self.submit_rendered_form(doc, theme_preference="dark")
        self.assertEqual(["dark"], stored(self.user))

    def test_the_three_switchers_use_distinct_radio_groups_and_ids(self):
        doc = self.get_page()

        switchers = doc("fieldset.sumo-theme-switcher")
        groups = [
            sorted({radio.get("name") for radio in s.find("input")}) for s in switchers.items()
        ]
        self.assertCountEqual(
            [["footer-theme"], ["profile-menu-theme"], ["theme_preference"]], groups
        )
        ids = [radio.get("id") for radio in switchers.find("input")]
        self.assertEqual(9, len(ids))
        for element_id in ids:
            self.assertEqual(1, len(doc(f'[id="{element_id}"]')), element_id)
