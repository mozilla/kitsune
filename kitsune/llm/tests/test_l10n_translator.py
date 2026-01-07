from unittest.mock import patch

from kitsune.llm.l10n.translator import (
    resolve_anchors,
    resolve_external_anchors,
    resolve_internal_anchors,
)
from kitsune.sumo.tests import TestCase
from kitsune.wiki.models import RevisionAnchorRecord
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DocumentFactory,
    RevisionAnchorRecordFactory,
)


class ResolveInternalAnchorsTestCase(TestCase):
    """Tests for the resolve_internal_anchors function."""

    def setUp(self):
        self.source_locale = "en-US"
        self.target_locale = "fr"

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    @patch("kitsune.wiki.parser.wiki_to_html")
    def test_resolve_single_internal_anchor(self, wiki_to_html_mock, get_anchor_map_mock):
        """Test resolving a single internal anchor reference."""
        source_content = "See the [[ #w_getting-started |getting started]] section."
        target_content = "Voir la section [[ #w_getting-started |pour commencer]]."

        get_anchor_map_mock.return_value = {
            "map": {"w_getting-started": "w_pour-commencer"},
            "explanation": "Mapped anchor",
        }

        result = resolve_internal_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        self.assertEqual(result, "Voir la section [[ #w_pour-commencer |pour commencer]].")

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    @patch("kitsune.wiki.parser.wiki_to_html")
    def test_resolve_multiple_internal_anchors(self, wiki_to_html_mock, get_anchor_map_mock):
        """Test resolving multiple internal anchor references."""
        source_content = "See [[  #w_intro|intro]] and [[#w_setup|setup]] sections."
        target_content = "Voir sections [[  #w_intro|introduction]] et [[#w_setup|configuration]]."

        get_anchor_map_mock.return_value = {
            "map": {"w_intro": "w_introduction", "w_setup": "w_configuration"},
            "explanation": "Mapped anchors",
        }

        result = resolve_internal_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        self.assertEqual(
            result,
            (
                "Voir sections [[  #w_introduction|introduction]] et"
                " [[#w_configuration|configuration]]."
            ),
        )

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    @patch("kitsune.wiki.parser.wiki_to_html")
    def test_resolve_substring_anchors(self, wiki_to_html_mock, get_anchor_map_mock):
        """Test that the replacement of anchors avoids substring issues."""
        source_content = "Links: [[#w_foo]] and [[#w_foo-bar]]."
        target_content = "Liens: [[#w_foo]] et [[#w_foo-bar]]."

        get_anchor_map_mock.return_value = {
            "map": {"w_foo": "w_fou", "w_foo-bar": "w_fou-barre"},
            "explanation": "Mapped anchors",
        }

        result = resolve_internal_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        self.assertEqual(result, "Liens: [[#w_fou]] et [[#w_fou-barre]].")

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    @patch("kitsune.wiki.parser.wiki_to_html")
    def test_no_internal_anchors_in_source(self, wiki_to_html_mock, get_anchor_map_mock):
        """Test that content without internal anchors is returned unchanged."""
        source_content = "This content has no internal anchors."
        target_content = "Ce contenu n'a pas d'ancres internes."

        result = resolve_internal_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        self.assertEqual(result, target_content)
        wiki_to_html_mock.assert_not_called()
        get_anchor_map_mock.assert_not_called()

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    @patch("kitsune.wiki.parser.wiki_to_html")
    def test_anchor_unchanged_when_same_in_both_locales(
        self, wiki_to_html_mock, get_anchor_map_mock
    ):
        """Test that anchors unchanged between locales are not replaced."""
        source_content = "See [[#w_firefox|Firefox]]."
        target_content = "Voir [[#w_firefox|Firefox]]."

        get_anchor_map_mock.return_value = {
            "map": {"w_firefox": "w_firefox"},
            "explanation": "Anchor unchanged",
        }

        result = resolve_internal_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        self.assertEqual(result, target_content)

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    @patch("kitsune.wiki.parser.wiki_to_html")
    def test_empty_target_content(self, wiki_to_html_mock, get_anchor_map_mock):
        """Test that empty target content is returned as-is."""
        source_content = "See [[#w_intro|intro]]."
        target_content = ""

        result = resolve_internal_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        self.assertEqual(result, "")
        wiki_to_html_mock.assert_not_called()
        get_anchor_map_mock.assert_not_called()

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    @patch("kitsune.wiki.parser.wiki_to_html")
    def test_empty_source_locale(self, wiki_to_html_mock, get_anchor_map_mock):
        """Test that empty source locale returns target content unchanged."""
        result = resolve_internal_anchors("", "content", "fr", "contenu")
        self.assertEqual(result, "contenu")
        wiki_to_html_mock.assert_not_called()
        get_anchor_map_mock.assert_not_called()


class ResolveExternalAnchorsTestCase(TestCase):
    """Tests for the resolve_external_anchors function."""

    def setUp(self):
        self.source_locale = "en-US"
        self.target_locale = "fr"

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    def test_resolve_single_external_anchor_with_translation(self, get_anchor_map_mock):
        """Test resolving an external anchor when the target document exists."""
        # Create source document with a revision, where the title of the source doc
        # contains characters that have a special meaning within regular expressions.
        source_doc = DocumentFactory(locale=self.source_locale, title="Firefox (Basics)")
        source_rev = ApprovedRevisionFactory(document=source_doc, is_ready_for_localization=True)

        # Create translated document
        target_doc = DocumentFactory(
            locale=self.target_locale, title="Firefox (de base)", parent=source_doc
        )
        ApprovedRevisionFactory(document=target_doc, based_on=source_rev)

        source_content = "See [[ Firefox (Basics)#w_getting-started|getting started]]."
        target_content = "Voir [[ Firefox (Basics)#w_getting-started|pour commencer]]."

        get_anchor_map_mock.return_value = {
            "map": {"w_getting-started": "w_pour-commencer"},
            "explanation": "Mapped anchor",
        }

        result = resolve_external_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        # Should translate both title and anchor
        self.assertEqual(result, "Voir [[ Firefox (de base)#w_pour-commencer|pour commencer]].")
        get_anchor_map_mock.assert_called_once()

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    def test_resolve_external_anchor_human_translated_title(self, get_anchor_map_mock):
        """Test when a human has already translated the title but not the anchor."""
        # Create source and target documents
        source_doc = DocumentFactory(locale=self.source_locale, title="Firefox Basics")
        source_rev = ApprovedRevisionFactory(document=source_doc, is_ready_for_localization=True)

        target_doc = DocumentFactory(
            locale=self.target_locale, title="Firefox de base", parent=source_doc
        )
        ApprovedRevisionFactory(document=target_doc, based_on=source_rev)

        source_content = "See [[Firefox Basics#w_getting-started |guide]]."
        # Somebody already translated the title but not the anchor
        target_content = "Voir [[Firefox de base#w_getting-started |guide]]."

        get_anchor_map_mock.return_value = {
            "map": {"w_getting-started": "w_pour-commencer"},
            "explanation": "Mapped anchor",
        }

        result = resolve_external_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        # Should update the anchor even though title was already translated
        self.assertEqual(result, "Voir [[Firefox de base#w_pour-commencer |guide]].")

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    def test_resolve_multiple_external_anchors_for_multiple_docs(self, get_anchor_map_mock):
        """Test resolving multiple anchors to each of multiple external documents."""
        source_doc = DocumentFactory(locale=self.source_locale, title="Cars")
        source_rev = ApprovedRevisionFactory(
            document=source_doc, content="Cars", is_ready_for_localization=True
        )
        target_doc = DocumentFactory(
            locale=self.target_locale, title="Voitures", parent=source_doc
        )
        target_rev = ApprovedRevisionFactory(document=target_doc, based_on=source_rev)

        source_doc_2 = DocumentFactory(locale=self.source_locale, title="Rockets")
        source_rev_2 = ApprovedRevisionFactory(
            document=source_doc_2, content="Rockets", is_ready_for_localization=True
        )
        target_doc_2 = DocumentFactory(
            locale=self.target_locale, title="Fusées", parent=source_doc_2
        )
        target_rev_2 = ApprovedRevisionFactory(document=target_doc_2, based_on=source_rev_2)

        source_content = (
            "See [[Cars#w_engine]], [[Cars#w_tires]],"
            " [[Rockets#w_propulsion]], and [[Rockets#w_payload]]."
        )
        target_content = (
            "Voir [[Cars#w_engine]], [[Cars#w_tires]],"
            " [[Rockets#w_propulsion]], et [[Rockets#w_payload]]."
        )

        cars_anchor_map = {
            "map": {"w_engine": "w_moteur", "w_tires": "w_pneus"},
            "explanation": "Mapped anchors for Cars",
        }

        rockets_anchor_map = {
            "map": {"w_payload": "w_charge-utile", "w_propulsion": "w_propulsion"},
            "explanation": "Mapped anchors for Rockets",
        }

        def get_anchor_map(source_locale, source_html, target_locale, target_html):
            return cars_anchor_map if "Cars" in source_html else rockets_anchor_map

        get_anchor_map_mock.side_effect = get_anchor_map

        result = resolve_external_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        self.assertEqual(
            result,
            (
                "Voir [[Voitures#w_moteur]], [[Voitures#w_pneus]],"
                " [[Fusées#w_propulsion]], et [[Fusées#w_charge-utile]]."
            ),
        )

        # Should only call get_anchor_map once per document
        self.assertEqual(get_anchor_map_mock.call_count, 2)

        # Should have created a RevisionAnchorRecord for each translated revision.
        anchor_record = RevisionAnchorRecord.objects.filter(revision=target_rev).first()
        self.assertIsNotNone(anchor_record)
        self.assertEqual(anchor_record.map, cars_anchor_map["map"])
        self.assertEqual(anchor_record.explanation, cars_anchor_map["explanation"])
        anchor_record_2 = RevisionAnchorRecord.objects.filter(revision=target_rev_2).first()
        self.assertIsNotNone(anchor_record_2)
        self.assertEqual(anchor_record_2.map, rockets_anchor_map["map"])
        self.assertEqual(anchor_record_2.explanation, rockets_anchor_map["explanation"])

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    def test_resolve_multiple_external_anchors_with_anchor_records(self, get_anchor_map_mock):
        """Test resolving multiple anchors with each already having anchor records."""
        source_doc = DocumentFactory(locale=self.source_locale, title="Cars")
        source_rev = ApprovedRevisionFactory(
            document=source_doc, content="Cars", is_ready_for_localization=True
        )
        target_doc = DocumentFactory(
            locale=self.target_locale, title="Voitures", parent=source_doc
        )
        target_rev = ApprovedRevisionFactory(document=target_doc, based_on=source_rev)

        source_doc_2 = DocumentFactory(locale=self.source_locale, title="Rockets")
        source_rev_2 = ApprovedRevisionFactory(
            document=source_doc_2, content="Rockets", is_ready_for_localization=True
        )
        target_doc_2 = DocumentFactory(
            locale=self.target_locale, title="Fusées", parent=source_doc_2
        )
        target_rev_2 = ApprovedRevisionFactory(document=target_doc_2, based_on=source_rev_2)

        source_content = (
            "See [[Cars#w_engine]], [[Cars#w_tires]],"
            " [[Rockets#w_propulsion]], and [[Rockets#w_payload]]."
        )
        target_content = (
            "Voir [[Cars#w_engine]], [[Cars#w_tires]],"
            " [[Rockets#w_propulsion]], et [[Rockets#w_payload]]."
        )

        RevisionAnchorRecordFactory(
            revision=target_rev,
            map={"w_engine": "w_moteur", "w_tires": "w_pneus"},
        )
        RevisionAnchorRecordFactory(
            revision=target_rev_2,
            map={"w_payload": "w_charge-utile", "w_propulsion": "w_propulsion"},
        )

        result = resolve_external_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        self.assertEqual(
            result,
            (
                "Voir [[Voitures#w_moteur]], [[Voitures#w_pneus]],"
                " [[Fusées#w_propulsion]], et [[Fusées#w_charge-utile]]."
            ),
        )

        # Since we already had an RevisionAnchorRecord object for the translation of each
        # of the external documents, we should have never called "get_anchor_map_mock".
        get_anchor_map_mock.assert_not_called()

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    def test_external_anchor_without_translation(self, get_anchor_map_mock):
        """Test that anchors to untranslated documents are left unchanged."""
        ApprovedRevisionFactory(
            is_ready_for_localization=True,
            document__title="Untranslated Doc",
            document__locale=self.source_locale,
        )

        source_content = "See [[Untranslated Doc#w_section|section]]."
        target_content = "Voir [[Untranslated Doc#w_section|section]]."

        result = resolve_external_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        # Should remain unchanged since there's no translation
        self.assertEqual(result, target_content)
        get_anchor_map_mock.assert_not_called()

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    def test_no_external_anchors_in_source(self, get_anchor_map_mock):
        """Test that content without external anchors is returned unchanged."""
        source_content = "This content has no external anchors."
        target_content = "Ce contenu n'a pas d'ancres externes."

        result = resolve_external_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        self.assertEqual(result, target_content)
        get_anchor_map_mock.assert_not_called()

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    def test_substring_external_anchors(self, get_anchor_map_mock):
        """Test that the replacement of external anchors avoids substring issues."""
        source_doc = DocumentFactory(locale=self.source_locale, title="Doc")
        source_rev = ApprovedRevisionFactory(document=source_doc, is_ready_for_localization=True)

        target_doc = DocumentFactory(locale=self.target_locale, title="Doc FR", parent=source_doc)
        ApprovedRevisionFactory(document=target_doc, based_on=source_rev)

        source_content = "See [[Doc#w_foo]] and [[Doc#w_foo_bar]]."
        target_content = "Voir [[Doc#w_foo]] et [[Doc#w_foo_bar]]."

        get_anchor_map_mock.return_value = {
            "map": {"w_foo": "w_fou", "w_foo_bar": "w_fou_barre"},
            "explanation": "Mapped anchors",
        }

        result = resolve_external_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        self.assertEqual(result, "Voir [[Doc FR#w_fou]] et [[Doc FR#w_fou_barre]].")
        get_anchor_map_mock.assert_called_once()


class ResolveAnchorsTestCase(TestCase):
    """Tests for the resolve_anchors function (orchestrator)."""

    def setUp(self):
        self.source_locale = "en-US"
        self.target_locale = "fr"

    @patch("kitsune.llm.l10n.translator.get_anchor_map")
    def test_resolve_anchors_integration_both_types(self, get_anchor_map_mock):
        """Integration test with both internal and external anchors."""
        # Create external document
        source_doc = DocumentFactory(locale=self.source_locale, title="External Doc")
        source_rev = ApprovedRevisionFactory(document=source_doc, is_ready_for_localization=True)

        target_doc = DocumentFactory(
            locale=self.target_locale, title="Doc Externe", parent=source_doc
        )
        ApprovedRevisionFactory(document=target_doc, based_on=source_rev)

        source_content = "See [[#w_intro|intro]] and [[External Doc#w_ext|external]]."
        target_content = "Voir [[#w_intro|introduction]] et [[External Doc#w_ext|externe]]."

        get_anchor_map_mock.side_effect = [
            {
                "map": {"w_intro": "w_introduction"},
                "explanation": "Mapped anchor",
            },
            {
                "map": {"w_ext": "w_externe"},
                "explanation": "Mapped anchor",
            },
        ]

        result = resolve_anchors(
            self.source_locale, source_content, self.target_locale, target_content
        )

        # Both internal and external anchors should be resolved
        self.assertEqual(
            result, "Voir [[#w_introduction|introduction]] et [[Doc Externe#w_externe|externe]]."
        )
        # Should call get_anchor_map once when resolving the internal anchors and one
        # more time (only one external document) when resolving the external anchors.
        self.assertEqual(get_anchor_map_mock.call_count, 2)
