from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from kitsune.llm.l10n.ui_labels.strings import github, shipped_locales
from kitsune.llm.l10n.ui_labels.strings.locales import get_catalog_locales, get_product_codes


class LocaleTests(SimpleTestCase):
    def test_catalog_locales(self):
        for code, expected in (
            ("fr", ("fr",)),
            ("pt_BR", ("pt-BR",)),
            ("zh-rCN", ("zh-CN",)),
            ("iw", ("he",)),
            ("nb-NO", ("no",)),
            ("es-rES", ("es",)),
            ("es-MX", ("es-MX",)),
            ("ta", ("ta", "ta-LK")),
            ("pt", ()),
            ("en-US", ()),
            ("ja-JP-mac", ()),
        ):
            with self.subTest(code):
                self.assertEqual(get_catalog_locales(code), expected)

    def test_product_codes_prefers_the_longer_code(self):
        self.assertEqual(
            get_product_codes(["sv_SE", "sv", "es", "es-ES", "fy_NL", "fy", "nb", "kab"]),
            {"sv": "sv_SE", "es": "es-ES", "fy-NL": "fy_NL", "no": "nb"},
        )


class ShippedTests(SimpleTestCase):
    def test_reading_each_kind_of_list(self):
        for read, text, expected in (
            (
                shipped_locales.first_words,
                "ach\nja-JP-mac osx\n\nfr\n",
                ["ach", "ja-JP-mac", "fr"],
            ),
            (
                shipped_locales.xcode_regions,
                'x = 1;\n\t\t\tknownRegions = (\n\t\t\t\ten,\n\t\t\t\tBase,\n\t\t\t\t"zh-Hans",\n\t\t\t);\n',
                ["en", "Base", "zh-Hans"],
            ),
            (
                shipped_locales.javascript_langs,
                "validKeys: ['langs'],\n  langs: [\n    'af',\n    'pt-BR',\n  ],\n",
                ["af", "pt-BR"],
            ),
            (
                shipped_locales.gradle_locale_filters,
                'androidResources {\n    localeFilters += listOf(\n        "ar",\n        "pt-rBR",\n    )\n}\n',
                ["ar", "pt-rBR"],
            ),
        ):
            with self.subTest(read.__name__):
                self.assertEqual(read(text), expected)

    @patch.object(shipped_locales.github, "get_paths")
    def test_android_ships_the_folders_with_strings(self, paths):
        paths.return_value = [
            "values-fr",
            "values-fr/strings.xml",
            "values-night/colors.xml",
            "values/strings.xml",
        ]
        self.assertEqual(shipped_locales.get_shipped_codes("firefox-android"), {"fr"})

    @patch.object(shipped_locales.github, "get_file_text")
    def test_a_list_that_names_no_sumo_locale_is_an_error(self, file_text):
        for text in ("", "This file moved to another folder.\n"):
            file_text.return_value = text
            with self.subTest(text), self.assertRaises(ValueError):
                shipped_locales.get_shipped_codes("firefox")

    @patch.object(github.requests, "get")
    @override_settings(UI_LABELS_GITHUB_TOKEN="secret")
    def test_the_token_only_goes_to_the_github_api(self, get):
        github.get_latest_commit("mozilla/fxa", "main")
        github.get_file_text("mozilla/fxa", "main", "README.md")
        github.get_tarball("mozilla/fxa", "abc")
        self.assertEqual(
            ["Authorization" in call.kwargs["headers"] for call in get.call_args_list],
            [True, False, False],
        )
