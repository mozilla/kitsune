from kitsune.llm.l10n.ui_labels.official import OfficialLabel, OfficialLabels
from kitsune.llm.l10n.ui_labels.owners import LabelOwner
from kitsune.llm.models import UISpotList, UIStringCatalog, UIStringSource
from kitsune.sumo.tests import TestCase

VIEW = ["menu:view", "a:view", "b:view"]
BOTH = ["a:view", "b:view"]


class OfficialLabelsTests(TestCase):
    def setUp(self):
        source = UIStringSource.objects.create(name="firefox-l10n")
        UISpotList.objects.create(
            owner="firefox",
            strings_by_text={
                "view": [
                    {"id": string_id, "text": "View", "spot": spot}
                    for string_id, spot in zip(VIEW, (0, 1, 1), strict=True)
                ],
                "help": [{"id": "menu:help", "text": "Help", "spot": 0}],
            },
        )
        for locale, strings in (
            (
                "fr",
                dict(zip(VIEW, ("Affichage", "Voir", "Voir"), strict=True))
                | {"menu:help": "Aide"},
            ),
            ("de", dict.fromkeys(VIEW, "Ansicht")),
            ("es", {"menu:view": "Ver", "a:view": "Vista", "menu:help": "Ayuda"}),
            ("es-MX", {"a:view": "Mirar", "menu:help": "Auxilio"}),
        ):
            UIStringCatalog.objects.create(
                owner="firefox", source=source, locale=locale, strings=strings
            )

    def test_the_rules_and_the_reasons_for_no_official_label(self):
        french, spanish = ("Affichage", "Voir"), ("Ver", "Vista")
        for locale, text, owner, spot, written, expected in (
            ("fr", "Help", "firefox", None, None, ("only one", "Aide", ("Aide",))),
            ("de", "View", "firefox", BOTH, "Sicht", ("only one", "Ansicht", ("Ansicht",))),
            ("fr", "View", "firefox", BOTH, "voir", ("spot", "Voir", french)),
            ("fr", "View", "firefox", BOTH, "Voir", ("kept", "Voir", french)),
            # The spot wins over an official label that belongs to another spot.
            ("fr", "View", "firefox", BOTH, "Affichage", ("spot", "Voir", french)),
            ("fr", "View", "firefox", [], "Affichage", ("kept", "Affichage", french)),
            # A label from Spanish as another country speaks it is official too.
            ("es", "Help", "firefox", None, "Auxilio", ("kept", "Auxilio", ("Ayuda",))),
            ("es", "View", "firefox", ["a:view"], "Mirar", ("kept", "Mirar", spanish)),
            ("fr", "View", "firefox", [], "Vue", ("unclear", "", french)),
            ("es", "View", "firefox", ["b:view"], None, ("not translated", "", spanish)),
            ("de", "Help", "firefox", None, None, ("not translated",)),
            ("pl", "View", "firefox", None, None, ("not shipped",)),
            ("fr", "Bookmarks", "firefox", None, None, ("no string",)),
            ("fr", "View", "relay", None, None, ("strings not loaded",)),
            ("fr", "View", "unknown", None, None, ("no owner",)),
        ):
            with self.subTest(locale=locale, text=text, owner=owner, spot=spot, written=written):
                owners = {0: LabelOwner("menu", text, owner, spot=spot)}
                self.assertEqual(
                    OfficialLabels(owners, locale).of(0, written), OfficialLabel(*expected)
                )
