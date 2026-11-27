import json
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from kitsune.llm.l10n.ui_labels import pairing
from kitsune.llm.l10n.ui_labels.owners import lookup
from kitsune.llm.l10n.ui_labels.report import Finding, check_article
from kitsune.llm.management.commands import ui_labels
from kitsune.llm.models import UISpotList, UIStringCatalog, UIStringSource
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory

OFFICIAL_LABELS = {"View": "Affichage", "Help": "Aide", "Tools": "Outils", "Save": "Enregistrer"}
ENGLISH = "Use {menu View}, {menu Help}, {menu Tools}, {button Save} and {button OK}."
FRENCH = "{menu Affichage}, {menu aide}, {menu Tools}, {button Sauver}, {button OK} et {button Annuler}."


class ReportTests(TestCase):
    def setUp(self):
        source = UIStringSource.objects.create(name="firefox-l10n")
        UISpotList.objects.create(
            owner="firefox",
            strings_by_text={
                text.lower(): [{"id": text, "text": text, "spot": 0}] for text in OFFICIAL_LABELS
            },
        )
        UIStringCatalog.objects.create(
            owner="firefox", source=source, locale="fr", strings=OFFICIAL_LABELS
        )
        old = ApprovedRevisionFactory(content="Use {menu View}.", is_ready_for_localization=True)
        self.article = old.document
        english = ApprovedRevisionFactory(
            document=self.article, content=ENGLISH, is_ready_for_localization=True
        )
        ApprovedRevisionFactory(
            document=DocumentFactory(locale="fr", parent=self.article),
            content=FRENCH,
            based_on=english,
        )
        ApprovedRevisionFactory(
            document=DocumentFactory(locale="de", parent=self.article),
            content="{menu Ansicht}.",
            based_on=old,
        )
        owners = ["firefox", "firefox", "firefox", "firefox", "unknown"]
        said = AIMessage(
            content=json.dumps(
                {
                    "answers": [
                        {"label": position, "owner": owner}
                        for position, owner in enumerate(owners)
                    ]
                }
            )
        )
        self.enterContext(
            patch.object(lookup, "get_llm", return_value=RunnableLambda(lambda messages: said))
        )
        self.enterContext(patch.object(lookup, "redis_client"))
        reply = AIMessage(content="T3>>>>E3\nT5>>>>none\n----\nSauver is an older word.")
        self.enterContext(
            patch.object(pairing, "get_llm", return_value=RunnableLambda(lambda messages: reply))
        )

    def test_each_label_of_an_up_to_date_translation_is_compared_with_its_official_label(self):
        slug = self.article.slug
        self.assertEqual(
            sorted(check_article(self.article)),
            sorted(
                [
                    Finding("de", slug, "translation out of date, not checked"),
                    Finding(
                        "fr",
                        slug,
                        "matches the official label",
                        "{menu Affichage}",
                        "View",
                        "firefox",
                        "Affichage",
                    ),
                    Finding(
                        "fr",
                        slug,
                        "matches the official label",
                        "{menu aide}",
                        "Help",
                        "firefox",
                        "Aide",
                    ),
                    Finding(
                        "fr", slug, "left in English", "{menu Tools}", "Tools", "firefox", "Outils"
                    ),
                    Finding(
                        "fr",
                        slug,
                        "differs from the official label",
                        "{button Sauver}",
                        "Save",
                        "firefox",
                        "Enregistrer",
                    ),
                    Finding(
                        "fr", slug, "no official label: no owner", "{button OK}", "OK", "unknown"
                    ),
                    Finding("fr", slug, "not paired with an English label", "{button Annuler}"),
                ]
            ),
        )

    def test_the_command_counts_per_locale_and_goes_on_after_an_article_that_fails(self):
        ApprovedRevisionFactory(content="Click {button OK}.", is_ready_for_localization=True)
        findings = [Finding("fr", "a", "left in English"), Finding("fr", "a", "left in English")]
        out = StringIO()

        with patch.object(ui_labels, "check_article", side_effect=[ValueError("no"), findings]):
            call_command("ui_labels", "report", "--workers", "1", stdout=out, stderr=StringIO())

        self.assertEqual(
            out.getvalue().split("\n"),
            [
                "",
                "fr",
                "       2  left in English",
                "",
                "1 of 2 articles failed and aren't counted.",
                "",
            ],
        )
