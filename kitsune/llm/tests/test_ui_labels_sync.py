import io
import tarfile
from unittest.mock import patch

import requests
from django.test import SimpleTestCase

from kitsune.llm.l10n.ui_labels.strings import sync as sync_module
from kitsune.llm.l10n.ui_labels.strings.sources import SOURCES
from kitsune.llm.l10n.ui_labels.strings.sync import sync
from kitsune.llm.models import UIStringCatalog, UIStringSource
from kitsune.sumo.tests import TestCase


class SourceTests(SimpleTestCase):
    def test_thunderbird_for_android_reads_its_own_android_and_compose_strings(self):
        [files] = SOURCES["thunderbird-android"].owner_files
        for path, expected in (
            (
                "legacy/ui/src/main/res/values/strings.xml",
                ("", "legacy/ui/src/main/res/values/strings.xml"),
            ),
            (
                "feature/a/src/commonMain/composeResources/values-pt-rBR/strings.xml",
                ("pt-rBR", "feature/a/src/commonMain/composeResources/values/strings.xml"),
            ),
            ("app-k9mail/src/main/res/values/strings.xml", None),
            ("app-thunderbird/src/beta/res/values/strings.xml", None),
            ("config/weblate/composeResources/values/strings.xml", None),
            ("legacy/ui/src/main/res/values/colors.xml", None),
        ):
            with self.subTest(path):
                self.assertEqual(files.match(path), expected)


class Download:
    """Stands in for the open response of a tarball download."""

    def __init__(self, files):
        self.raw = io.BytesIO()
        with tarfile.open(fileobj=self.raw, mode="w:gz") as archive:
            for path, text in files.items():
                member = tarfile.TarInfo(f"repo-abc123/{path}")
                member.size = len(text.encode())
                archive.addfile(member, io.BytesIO(text.encode()))
        self.raw.seek(0)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


SOURCE = SOURCES["fxa-content-server-l10n"]
FILES = {
    "locale/templates/app.ftl": "save = Save\n",
    "locale/fr/app.ftl": "save = A\n",
    "locale/pl/app.ftl": "save = B\n",
}


@patch.object(sync_module, "get_shipped_codes", return_value={"fr", "pl"})
@patch.object(sync_module.github, "get_tarball")
@patch.object(sync_module.github, "get_latest_commit", return_value="abc123")
class SyncTests(TestCase):
    def catalogs(self, **filters):
        return {
            (catalog.owner, catalog.locale): catalog.strings
            for catalog in UIStringCatalog.objects.filter(**filters)
        }

    def test_saves_english_and_shipped_locales_once_per_commit(self, latest_commit, tarball, _):
        tarball.return_value = Download(
            {
                "locale/templates/app.ftl": "# A button\nsave = Save\n",
                # The soft hyphen in this word is a line-breaking hint, and isn't kept.
                "locale/fr/app.ftl": "save = Enre\u00adgistrer\n",
                "locale/pl/app.ftl": "save = Zapisz\n",
                "locale/de/app.ftl": "save = Speichern\n",
                "README.md": "save = Not a string\n",
            }
        )

        self.assertTrue(sync(SOURCE))

        self.assertEqual(
            self.catalogs(),
            {
                ("mozilla-account", "en-US"): {"locale/app.ftl:save": "Save"},
                ("mozilla-account", "fr"): {"locale/app.ftl:save": "Enregistrer"},
                ("mozilla-account", "pl"): {"locale/app.ftl:save": "Zapisz"},
            },
        )
        english = UIStringCatalog.objects.get(locale="en-US")
        self.assertEqual(english.comments, {"locale/app.ftl:save": "A button"})
        self.assertEqual(UIStringSource.objects.get().commit, "abc123")

        self.assertFalse(sync(SOURCE))
        self.assertEqual(tarball.call_count, 1)

    def test_a_failed_sync_keeps_the_last_strings_and_the_next_one_reads_again(
        self, latest_commit, tarball, _
    ):
        tarball.return_value = Download(FILES)
        sync(SOURCE)
        latest_commit.side_effect = requests.ConnectionError("down")

        with self.assertRaises(requests.ConnectionError):
            sync(SOURCE)

        self.assertEqual(
            self.catalogs(locale="fr"), {("mozilla-account", "fr"): {"locale/app.ftl:save": "A"}}
        )
        record = UIStringSource.objects.get()
        self.assertEqual(record.commit, "abc123")
        self.assertIn("down", record.error)

        latest_commit.side_effect = None
        tarball.return_value = Download(FILES)

        self.assertTrue(sync(SOURCE))
        self.assertEqual(UIStringSource.objects.get().error, "")

    def test_a_download_that_breaks_halfway_saves_none_of_its_strings(
        self, latest_commit, tarball, _
    ):
        source = SOURCES["thunderbird-l10n"]
        path = "mail/messenger/menubar.ftl"
        tarball.return_value = Download({f"fr/{path}": "save = A\n", f"pl/{path}": "save = B\n"})
        sync(source)
        latest_commit.return_value = "def456"
        # French is saved when the download moves on to Polish. The third file is one too many.
        tarball.return_value = Download(
            {f"fr/{path}": "save = C\n", f"pl/{path}": "save = D\n", f"zu/{path}": "save = E\n"}
        )

        with patch.object(sync_module, "MAX_DOWNLOAD_SIZE", 20), self.assertRaises(ValueError):
            sync(source)

        self.assertEqual(
            self.catalogs(),
            {
                ("thunderbird", "fr"): {f"{path}:save": "A"},
                ("thunderbird", "pl"): {f"{path}:save": "B"},
            },
        )
        self.assertEqual(UIStringSource.objects.get().commit, "abc123")

    def test_missing_strings_are_recorded_and_the_rest_is_saved(self, latest_commit, tarball, _):
        tarball.return_value = Download(FILES)
        sync(SOURCE)
        latest_commit.return_value = "def456"

        for missing, french, files in (
            (
                "pl",
                "C",
                {"locale/templates/app.ftl": "save = Save\n", "locale/fr/app.ftl": "save = C\n"},
            ),
            (
                "en-US",
                "D",
                {
                    "moved/app.ftl": "save = Save\n",
                    "locale/fr/app.ftl": "save = D\n",
                    "locale/pl/app.ftl": "save = B\n",
                },
            ),
        ):
            with self.subTest(missing):
                UIStringSource.objects.update(fingerprint="")
                tarball.return_value = Download(files)

                self.assertTrue(sync(SOURCE))

                self.assertEqual(
                    {
                        locale: strings["locale/app.ftl:save"]
                        for (_, locale), strings in self.catalogs().items()
                    },
                    {"en-US": "Save", "fr": french, "pl": "B"},
                )
                record = UIStringSource.objects.get()
                self.assertEqual(record.commit, "def456")
                self.assertIn(missing, record.error)

    def test_a_locale_no_longer_shipped_is_removed(self, latest_commit, tarball, shipped_codes):
        tarball.return_value = Download(FILES)
        sync(SOURCE)
        shipped_codes.return_value = {"fr"}
        tarball.return_value = Download(FILES)

        self.assertTrue(sync(SOURCE))
        self.assertEqual(
            set(self.catalogs()), {("mozilla-account", "en-US"), ("mozilla-account", "fr")}
        )

    def test_each_owner_gets_its_own_brand_from_one_repository(self, latest_commit, tarball, _):
        def brand(name):
            return f"-brand-short-name = {name}\nname = {name}\n"

        for source, files in (
            (
                "thunderbird-l10n",
                {
                    "fr/mail/branding/tb_beta/brand.ftl": brand("Thunderbird Beta"),
                    "fr/mail/branding/thunderbird/brand.ftl": brand("Thunderbird"),
                    "pl/mail/branding/thunderbird/brand.ftl": brand("Thunderbird"),
                },
            ),
            (
                "enterprise-firefox-l10n",
                {"en-US/browser/branding/enterprise/brand.ftl": brand("Firefox Enterprise")},
            ),
            (
                "firefox-l10n",
                {
                    "fr/browser/branding/enterprise/brand.ftl": brand("Firefox Entreprise"),
                    "fr/browser/branding/official/brand.ftl": brand("Firefox"),
                    "fr/toolkit/toolkit/about.ftl": "about = À propos de { -brand-short-name }\n",
                    "pl/browser/branding/official/brand.ftl": brand("Firefox"),
                    "pl/toolkit/toolkit/about.ftl": "about = O programie { -brand-short-name }\n",
                },
            ),
        ):
            tarball.return_value = Download(files)
            sync(SOURCES[source])

        key = "toolkit/toolkit/about.ftl:about"
        texts = {
            owner_locale: strings[key]
            for owner_locale, strings in self.catalogs(source__name="firefox-l10n").items()
        }
        self.assertEqual(
            texts,
            {
                ("firefox", "fr"): "À propos de Firefox",
                ("firefox", "pl"): "O programie Firefox",
                ("firefox-enterprise", "fr"): "À propos de Firefox Entreprise",
                # Polish has no Enterprise brand of its own, so it shows the English one.
                ("firefox-enterprise", "pl"): "O programie Firefox Enterprise",
                ("thunderbird", "fr"): "À propos de Thunderbird",
                ("thunderbird", "pl"): "O programie Thunderbird",
            },
        )

    def test_a_new_commit_of_a_brand_provider_reads_its_dependents_again(
        self, latest_commit, tarball, _
    ):
        provider = {
            "en-US/browser/branding/enterprise/brand.ftl": "-brand-short-name = A\nb = B\n"
        }
        dependent = {"toolkit/about.ftl": "about = About { -brand-short-name }\nok = OK\n"}
        for source, files in (
            ("enterprise-firefox-l10n", provider),
            ("firefox-l10n-source", dependent),
        ):
            tarball.return_value = Download(files)
            sync(SOURCES[source])
        self.assertFalse(sync(SOURCES["firefox-l10n-source"]))

        latest_commit.return_value = "def456"
        tarball.return_value = Download(provider)
        sync(SOURCES["enterprise-firefox-l10n"])
        latest_commit.return_value = "abc123"
        tarball.return_value = Download(dependent)

        self.assertTrue(sync(SOURCES["firefox-l10n-source"]))

    def test_vpn_ships_the_locales_translated_enough(self, latest_commit, tarball, _):
        def xliff(**targets):
            units = "".join(
                f'<trans-unit id="{name}"><source>{name}</source>'
                + (f"<target>{target}</target>" if target else "")
                + "</trans-unit>"
                for name, target in targets.items()
            )
            return f'<xliff><file original="app"><body>{units}</body></file></xliff>'

        tarball.return_value = Download(
            {
                "en/mozillavpn.xliff": xliff(a="", b="", c=""),
                "fr/mozillavpn.xliff": xliff(a="A", b="B", c="C"),
                "pl/mozillavpn.xliff": xliff(a="A", b="", c=""),
                "pl/extras.xliff": xliff(d="D", e="E", f="F"),
            }
        )
        sync(SOURCES["mozilla-vpn-client-l10n"])

        self.assertEqual(set(self.catalogs()), {("mozilla-vpn", "en-US"), ("mozilla-vpn", "fr")})
