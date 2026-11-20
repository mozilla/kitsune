import json
from unittest.mock import patch

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from waffle.testutils import override_switch

from kitsune.llm.l10n import translator
from kitsune.llm.l10n.translator import translate
from kitsune.llm.l10n.ui_labels.owners import lookup
from kitsune.llm.l10n.ui_labels.translation import CheckedTranslation, TranslationLabels
from kitsune.llm.models import UISpotList, UIStringCatalog, UIStringSource
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory

ENGLISH = (
    "Click {menu View}, then {menu Help}. In Windows, open {menu Settings}. "
    "Set {pref browser.tabs.warnOnClose} and press {button OK}. Open {menu Settings}."
)
# Firefox's strings by English text, each with its French and Korean official label.
STRINGS = {
    "view": {"menu-view": ("Affichage", "보기"), "button-view": ("Vue", "뷰")},
    "help": {"menu-help": ("Aide", "도움말")},
    "settings": {"menu-settings": ("Paramètres", "설정")},
    "show": {"menu-show": ("Vue", "표시")},
}
CONFIG = "{pref browser.tabs.warnOnClose}"


class MachineTranslationTests(TestCase):
    def setUp(self):
        source = UIStringSource.objects.create(name="firefox-l10n")
        UISpotList.objects.create(
            owner="firefox",
            strings_by_text={
                text: [
                    {"id": string_id, "text": text.title(), "spot": spot}
                    for spot, string_id in enumerate(strings)
                ]
                for text, strings in STRINGS.items()
            },
        )
        for index, locale in enumerate(("fr", "ko")):
            UIStringCatalog.objects.create(
                owner="firefox",
                source=source,
                locale=locale,
                strings={
                    string_id: official[index]
                    for strings in STRINGS.values()
                    for string_id, official in strings.items()
                },
            )
        self.article = ApprovedRevisionFactory(
            document=DocumentFactory(products=[ProductFactory(slug="firefox")]),
            content=ENGLISH,
            is_ready_for_localization=True,
        ).document
        # View is in a spot, Windows' Settings has no owner, and Firefox has no "OK".
        # Position 3 is the config {pref}, which is never asked about.
        self.said = [
            {"label": 0, "owner": "firefox", "spot": "s1"},
            {"label": 1, "owner": "firefox"},
            {"label": 2, "owner": "unknown", "unknown_reason": "os"},
            {"label": 4, "owner": "firefox"},
            {"label": 5, "owner": "firefox"},
        ]
        self.owner_llm = self.enterContext(
            patch.object(
                lookup,
                "get_llm",
                return_value=RunnableLambda(
                    lambda messages: AIMessage(content=json.dumps({"answers": self.said}))
                ),
            )
        )

        self.enterContext(patch.object(lookup, "redis_client"))

    def translated(self, locale, content, article=None, **revision):
        article = article or self.article
        ApprovedRevisionFactory(
            document=article.translated_to(locale)
            or DocumentFactory(locale=locale, parent=article),
            content=content,
            based_on=article.latest_localizable_revision,
            **revision,
        )

    def test_the_llm_is_told_the_official_label_of_each_label_that_has_one(self):
        labels = TranslationLabels(self.article, "fr")

        # Settings has two answers in this article, so only the check deals with it.
        self.assertEqual(
            labels.for_prompt,
            [("{menu View}", "{menu Affichage}"), ("{menu Help}", "{menu Aide}")],
        )
        self.assertEqual(labels.config_prefs, [CONFIG])

        # What an earlier translation has doesn't change what we know: "Vue" is
        # official for another spot of View, and "Assistance" isn't official at all.
        self.translated("fr", "Cliquez sur {menu Vue}, puis {menu Assistance}.")
        self.assertEqual(
            TranslationLabels(self.article, "fr").for_prompt,
            [("{menu View}", "{menu Affichage}"), ("{menu Help}", "{menu Aide}")],
        )

    def test_an_earlier_official_label_settles_a_label_that_has_no_spot(self):
        self.said = [{"label": 0, "owner": "firefox"}, {"label": 1, "owner": "firefox"}]
        for english, expected in (
            # Nothing says which "View" this is, so what the translation has is kept.
            (
                "{menu View}, {menu Help}.",
                [("{menu View}", "{menu Vue}"), ("{menu Help}", "{menu Aide}")],
            ),
            # "Vue" is also official for Show, so it can't say which of the two it stands for.
            ("{menu View}, {menu Show}.", [("{menu Show}", "{menu Vue}")]),
        ):
            with self.subTest(english):
                article = ApprovedRevisionFactory(
                    content=english, is_ready_for_localization=True
                ).document
                self.translated("fr", "{menu Vue}.", article)
                self.assertEqual(TranslationLabels(article, "fr").for_prompt, expected)

    def test_the_check_gives_labels_left_in_english_their_official_label(self):
        for locale, translation, expected in (
            (
                "fr",
                "Cliquez sur {menu View}, puis {menu aide}. Dans Windows, ouvrez {menu Settings}. "
                "Réglez {pref browser.tabs.warnonclose}, {button D'accord}. Ouvrez {menu Settings}.",
                CheckedTranslation(
                    "Cliquez sur {menu Affichage}, puis {menu Aide}. Dans Windows, ouvrez "
                    "{menu Settings}. Réglez {pref browser.tabs.warnonclose}, {button D'accord}. "
                    "Ouvrez {menu Paramètres}.",
                    [
                        "{menu View} → {menu Affichage}",
                        "{menu aide} → {menu Aide}",
                        "{menu Settings} → {menu Paramètres}",
                    ],
                    [],
                    [],
                    [CONFIG],
                ),
            ),
            # "Vue" is official for another spot of View, so the spot's official label goes in.
            # A label the LLM made up, like "Assistance", can't be checked.
            (
                "fr",
                f"{{menu Vue}}, {{menu Assistance}}, {{menu Paramètres}}, {CONFIG}, {{menu Options}}.",
                CheckedTranslation(
                    "{menu Affichage}, {menu Assistance}, {menu Paramètres}, "
                    f"{CONFIG}, {{menu Options}}.",
                    ["{menu Vue} → {menu Affichage}"],
                    [],
                    ["{menu Help}"],
                    [],
                ),
            ),
            # The 를 was chosen for "Settings". 설정 would need 을.
            (
                "ko",
                f"{{menu Help}} 메뉴. {{menu Settings}}. {CONFIG}. {{menu Settings}}를 여세요.",
                CheckedTranslation(
                    f"{{menu 도움말}} 메뉴. {{menu Settings}}. {CONFIG}. {{menu Settings}}를 여세요.",
                    ["{menu Help} → {menu 도움말}"],
                    ["{menu Settings}"],
                    ["{menu View}"],
                    [],
                ),
            ),
        ):
            with self.subTest(translation):
                self.assertEqual(
                    TranslationLabels(self.article, locale).check(translation), expected
                )

    def test_a_problem_with_the_labels_does_not_stop_the_translation(self):
        reply = AIMessage(
            content="Cliquez {menu View}.<<<<translation-delimiter>>>>I translated it."
        )
        self.owner_llm.side_effect = RuntimeError("no LLM")

        with (
            patch.object(translator, "get_llm", return_value=RunnableLambda(lambda prompt: reply)),
            override_switch("official-ui-labels", active=True),
            patch.object(translator, "capture_exception") as capture_exception,
        ):
            content = translate(self.article, "fr")["content"]

        capture_exception.assert_called_once()
        self.assertEqual(content["translation"], "Cliquez {menu View}.")
        self.assertEqual(content["explanation"], "I translated it.")

    def test_an_official_label_that_would_break_the_markup_is_not_written(self):
        UIStringCatalog.objects.filter(locale="fr").update(strings={"menu-help": "Aide [F1]"})
        article = ApprovedRevisionFactory(
            content="{menu Help}.", is_ready_for_localization=True
        ).document
        labels = TranslationLabels(article, "fr")

        self.assertEqual(labels.for_prompt, [])
        checked = labels.check("{menu Help}.")
        self.assertEqual(checked.content, "{menu Help}.")
        self.assertIn(
            "{menu Help} has an official label we can't write, 'Aide [F1]'",
            labels.explain(checked),
        )

    def test_a_translation_gets_the_official_labels_only_when_the_switch_is_on(self):
        sent = []

        def llm(prompt):
            sent.append(prompt.to_messages()[0].content)
            return AIMessage(
                content="Cliquez {menu View}.<<<<translation-delimiter>>>>I translated it."
            )

        with patch.object(translator, "get_llm", return_value=RunnableLambda(llm)):
            today = translate(self.article, "fr")
            self.assertEqual(self.owner_llm.call_count, 0)
            with override_switch("official-ui-labels", active=True):
                official = translate(self.article, "fr")

        self.assertEqual(today["content"]["translation"], "Cliquez {menu View}.")
        # With nothing to say about labels, the prompt is today's, to the last space.
        self.assertIn("Always prefer the map value.\n\n# Task Instructions", sent[0])
        self.assertIn("into a final translation.\n6. In your response", sent[0])
        self.assertEqual(official["content"]["translation"], "Cliquez {menu Affichage}.")
        self.assertEqual(
            official["content"]["explanation"],
            "I translated it.\n\n"
            "UI labels: 3 of 5 have an official label.\n"
            "{menu View} → Affichage (firefox, one of 2 official labels, chosen by spot menu-view)\n"
            "{menu Help} → Aide (firefox, the only translation)\n"
            "{menu Settings} has no official label (unknown: os)\n"
            "{button OK} has no official label (firefox, no string)\n"
            "{menu Settings} → Paramètres (firefox, the only translation)\n"
            "Changed to the official label by the check: {menu View} → {menu Affichage}.\n"
            "Have an official label that the translation doesn't use: {menu Help}, {menu Settings}.\n"
            f"Config text that the translation changed: {CONFIG}.",
        )
        # Only the content's prompt has the official labels, and only with the switch on.
        told = [prompt for prompt in sent if "`{menu Help}` → `{menu Aide}`" in prompt]
        self.assertEqual(len(told), 1)
        self.assertIn(f"`{CONFIG}`", told[0])
