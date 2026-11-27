from datetime import timedelta

from django.utils import timezone

from kitsune.llm.l10n.ui_labels.strings.spots import (
    build_spot_list,
    build_spot_lists,
    get_strings_with_text,
    is_one_spot,
)
from kitsune.llm.models import UISpotList, UIStringCatalog, UIStringSource
from kitsune.sumo.tests import TestCase


class SpotListTests(TestCase):
    def test_strings_translated_alike_everywhere_share_a_spot(self):
        source = UIStringSource.objects.create(name="firefox-l10n")
        for locale, strings in (
            (
                "en-US",
                {
                    "menu:view": "View",
                    "passwords:view": "View",
                    "reports:view": "View",
                    "new:view": "View",
                    "dialog:view": "View…",
                    "menu:help": "Help",
                },
            ),
            ("fr", {"menu:view": "Affichage", "passwords:view": "Voir", "reports:view": "Voir"}),
            (
                "de",
                {"menu:view": "Ansicht", "passwords:view": "Ansicht", "reports:view": "Ansicht"},
            ),
            ("es-MX", {"passwords:view": "Ver", "reports:view": "Mirar"}),
        ):
            UIStringCatalog.objects.create(
                owner="firefox", source=source, locale=locale, strings=strings
            )

        build_spot_list("firefox")

        strings_by_text = UISpotList.objects.get(owner="firefox").strings_by_text
        self.assertEqual(set(strings_by_text), {"view", "help"})
        self.assertEqual(strings_by_text["help"], [{"id": "menu:help", "text": "Help", "spot": 0}])
        self.assertEqual(
            {string["id"]: (string["text"], string["spot"]) for string in strings_by_text["view"]},
            {
                "dialog:view": ("View…", 0),
                "menu:view": ("View", 1),
                # Not translated anywhere yet, so it can't disagree with the first "View".
                "new:view": ("View", 1),
                # French says something else here. The Mexican catalog isn't a SUMO locale.
                "passwords:view": ("View", 2),
                "reports:view": ("View", 2),
            },
        )
        # A label finds the strings with its exact text. Only when there are none
        # does it find those that differ in case or a last "…".
        found = get_strings_with_text(["View", "view"])["firefox"]
        self.assertNotIn("dialog:view", {string["id"] for string in found["View"]})
        self.assertIn("dialog:view", {string["id"] for string in found["view"]})

    def test_a_spot_list_is_built_again_only_after_its_owner_was_synced(self):
        now = timezone.now()
        for owner, synced_at in (
            ("firefox", now + timedelta(hours=1)),
            ("thunderbird", now - timedelta(hours=1)),
        ):
            source = UIStringSource.objects.create(name=owner, synced_at=synced_at)
            UIStringCatalog.objects.create(
                owner=owner, source=source, locale="en-US", strings={"menu:help": "Help"}
            )
            UISpotList.objects.create(owner=owner, strings_by_text={})

        build_spot_lists()

        self.assertEqual(
            dict(UISpotList.objects.values_list("owner", "strings_by_text")),
            {
                "firefox": {"help": [{"id": "menu:help", "text": "Help", "spot": 0}]},
                "thunderbird": {},
            },
        )

    def test_a_saved_spot_holds_until_it_splits_or_all_its_strings_are_gone(self):
        strings = [
            {"id": "a", "text": "View", "spot": 0},
            {"id": "b", "text": "View", "spot": 0},
            {"id": "c", "text": "View", "spot": 1},
        ]
        for string_ids, expected in (
            ({"a", "b"}, True),
            ({"a", "gone"}, True),
            ({"a", "c"}, False),
            ({"gone"}, False),
        ):
            with self.subTest(string_ids):
                self.assertEqual(is_one_spot(string_ids, strings), expected)
