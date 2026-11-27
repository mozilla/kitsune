from unittest.mock import patch

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from kitsune.llm.l10n.ui_labels import pairing
from kitsune.llm.l10n.ui_labels.labels import find_label_uses, find_labels
from kitsune.llm.l10n.ui_labels.official import OfficialLabels
from kitsune.llm.l10n.ui_labels.owners import LabelOwner
from kitsune.llm.l10n.ui_labels.pairing import get_pairs, get_text_pairs
from kitsune.llm.models import (
    UILabelPairs,
    UISpotList,
    UIStringCatalog,
    UIStringSource,
)
from kitsune.sumo.tests import TestCase, login_to_admin
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory

ENGLISH = "Click {menu View}, then {menu Help}. Press {button OK} or {button OK}."


class PairLabelsTests(TestCase):
    def setUp(self):
        source = UIStringSource.objects.create(name="firefox-l10n")
        UISpotList.objects.create(
            owner="firefox",
            strings_by_text={
                "view": [{"id": "menu:view", "text": "View", "spot": 0}],
                "help": [{"id": "menu:help", "text": "Help", "spot": 0}],
            },
        )
        UIStringCatalog.objects.create(
            owner="firefox",
            source=source,
            locale="fr",
            strings={"menu:view": "Affichage", "menu:help": "Aide"},
        )
        self.english = ApprovedRevisionFactory(content=ENGLISH)
        owners = {
            position: LabelOwner(use.kind, use.text, owner)
            for (position, use), owner in zip(
                find_labels(ENGLISH).items(),
                ("firefox", "firefox", "unknown", "unknown"),
                strict=True,
            )
        }
        self.official_labels = OfficialLabels(owners, "fr")
        self.french = DocumentFactory(locale="fr", parent=self.english.document)
        self.sent = []

    def pairs(self, content, reply=None):
        """Pair a French translation's labels, with the LLM giving the reply if it's asked."""
        translation = ApprovedRevisionFactory(
            document=self.french, content=content, based_on=self.english
        )

        def llm(prompt):
            self.sent.append(prompt.to_messages()[1].content)
            return AIMessage(content=reply)

        with patch.object(pairing, "get_llm", return_value=RunnableLambda(llm)):
            first = get_pairs(translation, self.official_labels)
            # The second time, the LLM's answer comes from the saved record.
            self.assertEqual(get_pairs(translation, self.official_labels), first)
        return first

    def test_labels_pair_by_their_text_without_the_llm(self):
        for content, expected in (
            # Still in English, an official label, and two labels with one text, in order.
            (
                "{button ok} ou {button OK}, {menu help}, {menu affichage…}.",
                {0: 2, 1: 3, 2: 1, 3: 0},
            ),
            # A label is left over, but no English label that has an official label is.
            ("{menu Affichage}, {menu Aide}, {button Valider}", {0: 0, 1: 1}),
        ):
            with self.subTest(content):
                self.assertEqual(self.pairs(content), expected)
        self.assertEqual(self.sent, [])

    def test_a_label_of_another_variant_of_spanish_pairs_by_text(self):
        source = UIStringSource.objects.get()
        for locale, text in (("es", "Ayuda"), ("es-MX", "Auxilio")):
            UIStringCatalog.objects.create(
                owner="firefox", source=source, locale=locale, strings={"menu:help": text}
            )
        spanish = OfficialLabels(self.official_labels.owners, "es")

        pairs = get_text_pairs(
            dict(enumerate(find_label_uses(ENGLISH))), find_labels("{menu Auxilio}."), spanish
        )

        self.assertEqual(pairs, {0: 1})

    def test_the_llm_pairs_what_text_leaves_over_and_is_asked_once(self):
        pairs = self.pairs(
            "Cliquez {menu Vue}, puis {menu Aide}. {button Annuler}",
            # The last two lines name labels that don't exist.
            "T0 >>>> E0\nt1>>>>e1\nT2>>>>none\nT7>>>>E0\nT2>>>>E9\n----\nVue is an old word. T0>>>>E1",
        )

        self.assertEqual(pairs, {0: 0, 1: 1})
        record = UILabelPairs.objects.get()
        self.assertEqual(record.explanation, "Vue is an old word. T0>>>>E1")
        self.assertEqual(
            self.sent,
            [
                "English article:\n"
                "Click ⟦E0⟧{menu View}, then ⟦E1⟧{menu Help}. "
                "Press ⟦E2⟧{button OK} or ⟦E3⟧{button OK}.\n\n"
                "Translation into French:\n"
                "Cliquez ⟦T0⟧{menu Vue}, puis ⟦T1⟧{menu Aide}. ⟦T2⟧{button Annuler}"
            ],
        )

    def test_the_llm_wins_over_a_pair_by_text(self):
        # By text, {menu Aide} pairs with Help.
        for reply, expected in (
            # The LLM says it stands for View.
            ("T0>>>>E0\nT1>>>>none", {0: 0}),
            # The LLM gives Help to the other label.
            ("T1>>>>E1", {1: 1}),
            # The LLM says nothing we can read, so the pair by text stands.
            ("I can't tell.", {0: 1}),
        ):
            with self.subTest(reply):
                self.assertEqual(
                    self.pairs("Cliquez {menu Aide}, puis {menu Vue}.", reply), expected
                )

    def test_the_admin_shows_the_pairs_of_a_translation(self):
        # The second line names an English label that doesn't exist.
        self.pairs(
            "Cliquez {menu Vue}. {button Annuler}", "T0>>>>E1\nT1>>>>E9\n----\nAn old word."
        )
        login_to_admin(self.client, UserFactory(is_staff=True, is_superuser=True))

        record = UILabelPairs.objects.get()
        shown = self.client.get(reverse("admin:llm_uilabelpairs_change", args=[record.pk]))

        self.assertContains(
            shown, "T0  {menu Vue} → E1  {menu Help}\nT1  {button Annuler} → E9  ?</pre>"
        )
        self.assertContains(shown, "An old word.")
