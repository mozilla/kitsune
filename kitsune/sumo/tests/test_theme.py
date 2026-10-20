import base64
import hashlib
from contextlib import contextmanager, nullcontext
from pathlib import Path

from django.conf import settings
from django.test import Client
from django.utils.translation import trans_real
from pyquery import PyQuery as pq
from waffle.testutils import override_flag

from kitsune.sumo import theme
from kitsune.sumo.tests import TestCase
from kitsune.sumo.tests.test_middleware import csp_directives
from kitsune.sumo.theme import DARK_MODE_FLAG
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory
from kitsune.users.theme import set_theme_preference

SWITCHER = "fieldset.sumo-theme-switcher"
FOOTER_SWITCHER = f".mzp-c-footer-secondary {SWITCHER}"
MENU_SWITCHER = f"#mzp-c-menu-panel-profile {SWITCHER}"
THEME_ATTRIBUTES = (
    "data-theme",
    "data-theme-preference",
    "data-theme-owner",
    "data-theme-endpoint",
)


def sha256_source(text):
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return f"'sha256-{base64.b64encode(digest).decode('ascii')}'"


@contextmanager
def translated_strings(locale, strings):
    catalog = trans_real.translation(locale)._catalog
    for msgid, msgstr in strings.items():
        catalog[msgid] = msgstr
    try:
        yield
    finally:
        trans_real._translations.pop(locale, None)


class HeadScriptTests(TestCase):
    def test_setting_is_the_text_of_the_file(self):
        source = Path(theme.__file__).with_name("theme_head.js").read_bytes()

        self.assertEqual(source.decode("utf-8"), settings.HEAD_SCRIPT)

    def test_script_is_safe_to_inline_verbatim(self):
        # Browsers normalize CRLF before hashing, so a CRLF checkout would void the hash.
        self.assertNotIn("\r", settings.HEAD_SCRIPT)
        self.assertNotIn("</script", settings.HEAD_SCRIPT.lower())
        self.assertNotIn("<!--", settings.HEAD_SCRIPT)


class ThemePageTests(TestCase):
    def render(self, client, path=None):
        response = client.get(path or reverse("home"), follow=True)
        self.assertEqual(200, response.status_code)
        return response, pq(response.content, parser="html")

    def test_flag_off_renders_no_theme_markup(self):
        user = UserFactory()
        set_theme_preference(user, "dark")
        signed_in = Client()
        signed_in.force_login(user)
        flags = {
            "missing": nullcontext,
            "off": lambda: override_flag(DARK_MODE_FLAG, active=False),
        }

        for flag, flag_state in flags.items():
            for label, client in (("anonymous", Client()), ("signed in", signed_in)):
                with self.subTest(flag=flag, user=label), flag_state():
                    response, doc = self.render(client)

                    content = response.content.decode()
                    self.assertNotIn(settings.HEAD_SCRIPT, content)
                    self.assertNotIn("themeSwitcher", content)
                    for attribute in THEME_ATTRIBUTES:
                        self.assertNotIn(attribute, doc("html")[0].attrib)
                    self.assertEqual(
                        ["#ffffff"],
                        [meta.get("content") for meta in doc('meta[name="theme-color"]')],
                    )

    @override_flag(DARK_MODE_FLAG, active=True)
    def test_flag_on_inlines_the_script_first_in_head_and_allows_it_by_hash(self):
        response, doc = self.render(Client())

        first = doc("head")[0][0]
        self.assertEqual("script", first.tag)
        self.assertEqual(settings.HEAD_SCRIPT, first.text)
        self.assertIn(f"<script>{settings.HEAD_SCRIPT}</script>", response.content.decode())
        script_src = csp_directives(response["Content-Security-Policy"])["script-src"]
        self.assertIn(sha256_source(first.text), script_src)
        # The head script creates theme-color with the resolved color.
        self.assertEqual(0, len(doc('meta[name="theme-color"]')))

    @override_flag(DARK_MODE_FLAG, active=True)
    def test_anonymous_page_carries_no_server_rendered_theme(self):
        _, doc = self.render(Client())

        for attribute in THEME_ATTRIBUTES:
            self.assertNotIn(attribute, doc("html")[0].attrib)
        self.assertEqual(1, len(doc(SWITCHER)))
        self.assertEqual(1, len(doc(FOOTER_SWITCHER)))
        self.assertEqual(0, len(doc(f"{SWITCHER} input[checked]")))

    @override_flag(DARK_MODE_FLAG, active=True)
    def test_signed_in_page_has_hidden_footer_and_menu_switchers(self):
        self.client.force_login(UserFactory())

        response, doc = self.render(self.client)

        # Raw HTML, because the parser may drop @-prefixed attributes.
        self.assertEqual(
            2, response.content.decode().count('x-data="themeSwitcher" @change="choose"')
        )
        for selector, variant in ((FOOTER_SWITCHER, "footer"), (MENU_SWITCHER, "menu")):
            with self.subTest(variant):
                switcher = doc(selector)
                self.assertEqual(1, len(switcher))
                self.assertEqual(
                    ["sumo-theme-switcher", f"is-{variant}"], switcher.attr("class").split()
                )
                self.assertIn("hidden", switcher[0].attrib)
                self.assertEqual("Appearance", switcher.children("legend").text())
                radios = switcher.find("input")
                self.assertEqual(["radio"] * 3, [radio.get("type") for radio in radios])
                self.assertEqual(
                    ["system", "light", "dark"], [radio.get("value") for radio in radios]
                )
                self.assertEqual(
                    ["System", "Light", "Dark"],
                    [switcher.find(f'label[for="{radio.get("id")}"]').text() for radio in radios],
                )

    @override_flag(DARK_MODE_FLAG, active=True)
    def test_switcher_labels_are_translated(self):
        translations = {
            "Appearance": "Darstellung",
            "System": "Systemvorgabe",
            "Light": "Hell",
            "Dark": "Dunkel",
        }
        with translated_strings("de", translations):
            _, doc = self.render(Client(), reverse("home", locale="de"))

        switcher = doc(FOOTER_SWITCHER)
        self.assertEqual("Darstellung", switcher.children("legend").text())
        self.assertEqual(
            ["Systemvorgabe", "Hell", "Dunkel"], [label.text for label in switcher.find("label")]
        )
