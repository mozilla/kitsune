from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.test.utils import override_settings
from django.utils.timezone import now as timezone_now

from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory
from kitsune.wiki.config import MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE, TYPO_SIGNIFICANCE
from kitsune.wiki.services import (
    HybridTranslationService,
    MissingTranslationService,
    StaleTranslationService,
    TranslationQueryBuilder,
)
from kitsune.wiki.strategies import TranslationMethod, TranslationStrategyFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory, RevisionFactory

APPROVED_MSG = "Automatically approved because it was not reviewed within 72 hours."
REJECTED_MSG = "No longer relevant."


class HybridTranslationServiceTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sumo_bot = Profile.get_sumo_bot()
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        four_days_ago = now - timedelta(days=4)
        six_days_ago = now - timedelta(days=6)
        seven_days_ago = now - timedelta(days=7)

        self.doc1_en = DocumentFactory()
        rev1_en = ApprovedRevisionFactory(
            document=self.doc1_en,
            created=datetime(2024, 5, 1),
            reviewed=datetime(2024, 5, 2),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        rev2_en = ApprovedRevisionFactory(
            document=self.doc1_en,
            created=datetime(2024, 5, 5),
            reviewed=datetime(2024, 5, 6),
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        ApprovedRevisionFactory(
            document=self.doc1_en,
            created=datetime(2024, 6, 7),
            reviewed=datetime(2024, 6, 8),
            significance=TYPO_SIGNIFICANCE,
            is_ready_for_localization=False,
        )

        doc1_es = DocumentFactory(parent=self.doc1_en, locale="es")
        ApprovedRevisionFactory(
            document=doc1_es,
            based_on=rev1_en,
            created=datetime(2024, 5, 3),
            reviewed=datetime(2024, 5, 4),
        )
        self.rev2_es = RevisionFactory(
            document=doc1_es,
            based_on=rev2_en,
            creator=self.sumo_bot,
            created=two_days_ago,
            reviewed=None,
        )

        doc1_ro = DocumentFactory(parent=self.doc1_en, locale="ro")
        self.rev1_ro = RevisionFactory(
            document=doc1_ro,
            based_on=rev2_en,
            creator=self.sumo_bot,
            created=two_days_ago,
            reviewed=None,
        )
        ApprovedRevisionFactory(
            document=doc1_ro,
            based_on=rev2_en,
            created=one_day_ago,
            reviewed=one_day_ago,
        )

        self.doc1_el = DocumentFactory(parent=self.doc1_en, locale="el")
        self.rev1_el = RevisionFactory(
            document=self.doc1_el,
            based_on=rev1_en,
            creator=self.sumo_bot,
            created=datetime(2024, 5, 3),
            reviewed=None,
        )
        self.rev2_el = RevisionFactory(
            document=self.doc1_el,
            based_on=rev2_en,
            creator=self.sumo_bot,
            created=four_days_ago,
            reviewed=None,
        )

        self.doc1_ja = DocumentFactory(parent=self.doc1_en, locale="ja")
        self.rev1_ja = RevisionFactory(
            document=self.doc1_ja,
            based_on=rev1_en,
            creator=self.sumo_bot,
            created=datetime(2024, 5, 3),
            reviewed=None,
        )
        self.rev2_ja = RevisionFactory(
            document=self.doc1_ja,
            based_on=rev2_en,
            creator=self.sumo_bot,
            created=four_days_ago,
            reviewed=None,
        )

        doc1_it = DocumentFactory(parent=self.doc1_en, locale="it")
        self.rev1_it = RevisionFactory(
            document=doc1_it,
            based_on=rev2_en,
            creator=self.sumo_bot,
            created=seven_days_ago,
            reviewed=six_days_ago,
            reviewer=UserFactory(),
        )
        RevisionFactory(
            document=doc1_it,
            based_on=rev2_en,
            creator=UserFactory(),
            created=four_days_ago,
            reviewed=None,
        )

        self.doc2_en = DocumentFactory()
        rev1_en_2 = ApprovedRevisionFactory(
            document=self.doc2_en,
            created=datetime(2024, 5, 1),
            reviewed=datetime(2024, 5, 2),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        rev2_en_2 = ApprovedRevisionFactory(
            document=self.doc2_en,
            created=datetime(2024, 5, 5),
            reviewed=datetime(2024, 5, 6),
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        ApprovedRevisionFactory(
            document=self.doc2_en,
            created=datetime(2024, 6, 7),
            reviewed=datetime(2024, 6, 8),
            significance=TYPO_SIGNIFICANCE,
            is_ready_for_localization=False,
        )

        doc2_es = DocumentFactory(parent=self.doc2_en, locale="es")
        ApprovedRevisionFactory(
            document=doc2_es,
            based_on=rev1_en_2,
            created=datetime(2024, 5, 3),
            reviewed=datetime(2024, 5, 4),
        )
        self.rev2_es_2 = RevisionFactory(
            document=doc2_es,
            based_on=rev2_en_2,
            creator=self.sumo_bot,
            created=two_days_ago,
            reviewed=None,
        )

        doc2_ro = DocumentFactory(parent=self.doc2_en, locale="ro")
        self.rev1_ro_2 = RevisionFactory(
            document=doc2_ro,
            based_on=rev2_en_2,
            creator=self.sumo_bot,
            created=two_days_ago,
            reviewed=None,
        )
        ApprovedRevisionFactory(
            document=doc2_ro,
            based_on=rev2_en_2,
            created=one_day_ago,
            reviewed=one_day_ago,
        )

        doc2_el = DocumentFactory(parent=self.doc2_en, locale="el")
        self.rev1_el_2 = RevisionFactory(
            document=doc2_el,
            based_on=rev1_en_2,
            creator=self.sumo_bot,
            created=datetime(2024, 5, 3),
            reviewed=None,
        )
        self.rev2_el_2 = RevisionFactory(
            document=doc2_el,
            based_on=rev2_en_2,
            creator=self.sumo_bot,
            created=four_days_ago,
            reviewed=None,
        )

        doc2_ja = DocumentFactory(parent=self.doc2_en, locale="ja")
        self.rev1_ja_2 = RevisionFactory(
            document=doc2_ja,
            based_on=rev1_en_2,
            creator=self.sumo_bot,
            created=datetime(2024, 5, 3),
            reviewed=None,
        )
        self.rev2_ja_2 = RevisionFactory(
            document=doc2_ja,
            based_on=rev2_en_2,
            creator=self.sumo_bot,
            created=four_days_ago,
            reviewed=None,
        )

        doc2_it = DocumentFactory(parent=self.doc2_en, locale="it")
        self.rev1_it_2 = RevisionFactory(
            document=doc2_it,
            based_on=rev2_en_2,
            creator=self.sumo_bot,
            created=seven_days_ago,
            reviewed=six_days_ago,
            reviewer=UserFactory(),
        )
        RevisionFactory(
            document=doc2_it,
            based_on=rev2_en_2,
            creator=UserFactory(),
            created=four_days_ago,
            reviewed=None,
        )

    @override_settings(
        HYBRID_REVIEW_GRACE_PERIOD=72,
        HYBRID_ENABLED_LOCALES=["el", "ro", "es", "it", "de", "ja"],
    )
    def test_reject_obsolete_translations_with_default_doc1(self):
        revs = (
            self.rev1_el,
            self.rev2_el,
            self.rev2_es,
            self.rev1_ja,
            self.rev2_ja,
            self.rev1_ro,
            self.rev1_it,
            self.rev1_el_2,
            self.rev2_el_2,
            self.rev2_es_2,
            self.rev1_ja_2,
            self.rev2_ja_2,
            self.rev1_ro_2,
            self.rev1_it_2,
        )

        datetime_prior_to_test = timezone_now()

        HybridTranslationService().reject_obsolete_translations(self.doc1_en)

        for rev in revs:
            rev.refresh_from_db()

        # The first Greek and Japanese revisions have been rejected because they're out-of-date,
        # but only the revision within the context of "doc1_en".
        self.assertFalse(self.rev1_el.is_approved)
        self.assertTrue(self.rev1_el.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_el.reviewer, self.sumo_bot)
        self.assertTrue(self.rev1_el.comment.endswith("\n" + REJECTED_MSG))

        self.assertFalse(self.rev1_ja.is_approved)
        self.assertTrue(self.rev1_ja.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_ja.reviewer, self.sumo_bot)
        self.assertTrue(self.rev1_ja.comment.endswith("\n" + REJECTED_MSG))

        # The first Romanian revision has been rejected because it was superseded
        # within its review grace period, but only the revision within the context
        # of "doc1_en".
        self.assertFalse(self.rev1_ro.is_approved)
        self.assertTrue(self.rev1_ro.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_ro.reviewer, self.sumo_bot)
        self.assertTrue(self.rev1_ro.comment.endswith("\n" + REJECTED_MSG))

        # These revisions should not have been touched.
        for rev in (
            self.rev2_el,
            self.rev1_el_2,
            self.rev2_el_2,
            self.rev2_ja,
            self.rev1_ja_2,
            self.rev2_ja_2,
            self.rev2_es,
            self.rev2_es_2,
            self.rev1_ro_2,
        ):
            self.assertIsNone(rev.reviewed)
            self.assertFalse(rev.is_approved)

        self.assertFalse(self.rev1_it.is_approved)
        self.assertTrue(self.rev1_it.reviewed < datetime_prior_to_test)
        self.assertFalse(self.rev1_it_2.is_approved)
        self.assertTrue(self.rev1_it_2.reviewed < datetime_prior_to_test)

    @override_settings(
        HYBRID_REVIEW_GRACE_PERIOD=72,
        HYBRID_ENABLED_LOCALES=["el", "ro", "es", "it", "de", "ja"],
    )
    def test_reject_obsolete_translations_with_default_doc2(self):
        revs = (
            self.rev1_el,
            self.rev2_el,
            self.rev2_es,
            self.rev1_ja,
            self.rev2_ja,
            self.rev1_ro,
            self.rev1_it,
            self.rev1_el_2,
            self.rev2_el_2,
            self.rev2_es_2,
            self.rev1_ja_2,
            self.rev2_ja_2,
            self.rev1_ro_2,
            self.rev1_it_2,
        )

        datetime_prior_to_test = timezone_now()

        HybridTranslationService().reject_obsolete_translations(self.doc2_en)

        for rev in revs:
            rev.refresh_from_db()

        # The first Greek and Japanese revisions have been rejected because they're
        # out-of-date, but only the revision within the context of "doc2_en".
        self.assertFalse(self.rev1_el_2.is_approved)
        self.assertTrue(self.rev1_el_2.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_el_2.reviewer, self.sumo_bot)
        self.assertTrue(self.rev1_el_2.comment.endswith("\n" + REJECTED_MSG))

        self.assertFalse(self.rev1_ja_2.is_approved)
        self.assertTrue(self.rev1_ja_2.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_ja_2.reviewer, self.sumo_bot)
        self.assertTrue(self.rev1_ja_2.comment.endswith("\n" + REJECTED_MSG))

        # The first Romanian revision has been rejected because it was superseded
        # within its review grace period, but only the revision within the context
        # of "doc2_en".
        self.assertFalse(self.rev1_ro_2.is_approved)
        self.assertTrue(self.rev1_ro_2.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_ro_2.reviewer, self.sumo_bot)
        self.assertTrue(self.rev1_ro_2.comment.endswith("\n" + REJECTED_MSG))

        # These revisions should not have been touched.
        for rev in (
            self.rev1_el,
            self.rev2_el,
            self.rev2_el_2,
            self.rev1_ja,
            self.rev2_ja,
            self.rev2_ja_2,
            self.rev2_es,
            self.rev2_es_2,
            self.rev1_ro,
        ):
            self.assertIsNone(rev.reviewed)
            self.assertFalse(rev.is_approved)

        self.assertFalse(self.rev1_it_2.is_approved)
        self.assertTrue(self.rev1_it_2.reviewed < datetime_prior_to_test)
        self.assertFalse(self.rev1_it.is_approved)
        self.assertTrue(self.rev1_it.reviewed < datetime_prior_to_test)

    @override_settings(
        HYBRID_REVIEW_GRACE_PERIOD=72,
        HYBRID_ENABLED_LOCALES=["el", "ro", "es", "it", "de", "ja"],
    )
    def test_reject_obsolete_translations_with_doc1_el(self):
        revs = (
            self.rev1_el,
            self.rev2_el,
            self.rev2_es,
            self.rev1_ja,
            self.rev2_ja,
            self.rev1_ro,
            self.rev1_it,
            self.rev1_el_2,
            self.rev2_el_2,
            self.rev2_es_2,
            self.rev1_ja_2,
            self.rev2_ja_2,
            self.rev1_ro_2,
            self.rev1_it_2,
        )

        datetime_prior_to_test = timezone_now()

        HybridTranslationService().reject_obsolete_translations(self.doc1_el)

        for rev in revs:
            rev.refresh_from_db()

        # The first Greek revision has been rejected because it's out-of-date,
        # but only the revision within the context of "doc1_el".
        self.assertFalse(self.rev1_el.is_approved)
        self.assertTrue(self.rev1_el.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_el.reviewer, self.sumo_bot)
        self.assertTrue(self.rev1_el.comment.endswith("\n" + REJECTED_MSG))

        for rev in revs:
            if rev == self.rev1_el:
                continue
            self.assertFalse(rev.is_approved)
            if rev in (self.rev1_it, self.rev1_it_2):
                self.assertTrue(rev.reviewed < datetime_prior_to_test)
            else:
                self.assertIsNone(rev.reviewed)

    @override_settings(
        HYBRID_REVIEW_GRACE_PERIOD=72,
        HYBRID_ENABLED_LOCALES=["el", "ro", "es", "it", "de", "ja"],
    )
    def test_publish_pending_translations(self):
        revs = (
            self.rev1_el,
            self.rev2_el,
            self.rev2_es,
            self.rev1_ja,
            self.rev2_ja,
            self.rev1_ro,
            self.rev1_it,
            self.rev1_el_2,
            self.rev2_el_2,
            self.rev2_es_2,
            self.rev1_ja_2,
            self.rev2_ja_2,
            self.rev1_ro_2,
            self.rev1_it_2,
        )

        datetime_prior_to_test = timezone_now()

        HybridTranslationService().publish_pending_translations()

        for rev in revs:
            rev.refresh_from_db()

        # The second Greek and Japanese revisions have been approved because they're up-to-date
        # and the review grace period has expired.
        for rev in (self.rev2_el, self.rev2_el_2, self.rev2_ja, self.rev2_ja_2):
            self.assertTrue(rev.is_approved)
            self.assertTrue(rev.reviewed > datetime_prior_to_test)
            self.assertEqual(rev.reviewer, self.sumo_bot)
            self.assertTrue(rev.comment.endswith("\n" + APPROVED_MSG))

        # These revisions should have remained untouched.
        for rev in (self.rev2_es, self.rev2_es_2, self.rev1_ro, self.rev1_ro_2):
            self.assertFalse(rev.is_approved)
            self.assertIsNone(rev.reviewed)

        for rev in (self.rev1_it, self.rev1_it_2):
            self.assertFalse(rev.is_approved)
            self.assertTrue(rev.reviewed < datetime_prior_to_test)

        # These revisions have been made obsolete via the post-save signal
        # to  the "reject_obsolete_translations()" receiver.
        for rev in (self.rev1_el, self.rev1_el_2, self.rev1_ja, self.rev1_ja_2):
            self.assertFalse(rev.is_approved)
            self.assertTrue(rev.reviewed > datetime_prior_to_test)


class TranslationQueryBuilderTests(TestCase):
    """Tests for TranslationQueryBuilder."""

    def setUp(self):
        super().setUp()
        self.query_builder = TranslationQueryBuilder()
        self.sumo_bot = Profile.get_sumo_bot()

        # Create English documents
        self.doc1_en = DocumentFactory(is_localizable=True, is_archived=False)
        self.rev1_en = ApprovedRevisionFactory(
            document=self.doc1_en,
            created=datetime(2024, 1, 1),
            reviewed=datetime(2024, 1, 2),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )

        self.doc2_en = DocumentFactory(is_localizable=True, is_archived=True)
        self.rev2_en = ApprovedRevisionFactory(
            document=self.doc2_en,
            created=datetime(2024, 1, 1),
            reviewed=datetime(2024, 1, 2),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )

        self.doc3_en = DocumentFactory(is_localizable=True, is_archived=False)
        self.rev3_en = ApprovedRevisionFactory(
            document=self.doc3_en,
            created=datetime(2024, 1, 1),
            reviewed=datetime(2024, 1, 2),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es", "ro"],
        AI_ENABLED_LOCALES=["de", "fr"],
        STALE_TRANSLATION_THRESHOLD_DAYS=30,
    )
    def test_get_stale_docs_hybrid(self):
        """Test finding stale translations in HYBRID locales (non-archived only)."""
        # Create old translation in HYBRID locale
        doc1_es = DocumentFactory(parent=self.doc1_en, locale="es")
        old_date = datetime.now() - timedelta(days=35)
        ApprovedRevisionFactory(
            document=doc1_es,
            based_on=self.rev1_en,
            created=old_date,
            reviewed=old_date,
        )

        # Create new revision in English to make translation stale
        ApprovedRevisionFactory(
            document=self.doc1_en,
            created=datetime.now() - timedelta(days=1),
            reviewed=datetime.now() - timedelta(days=1),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )

        # Create old translation for archived document (should NOT appear)
        doc2_es = DocumentFactory(parent=self.doc2_en, locale="es")
        ApprovedRevisionFactory(
            document=doc2_es,
            based_on=self.rev2_en,
            created=old_date,
            reviewed=old_date,
        )

        results = self.query_builder.get_stale_docs_hybrid(limit=10)

        # Should only find non-archived document
        self.assertEqual(len(results), 1)
        english_doc, translation_doc, locale = results[0]
        self.assertEqual(english_doc.id, self.doc1_en.id)
        self.assertEqual(translation_doc.locale, "es")
        self.assertFalse(english_doc.is_archived)

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es", "ro"],
        AI_ENABLED_LOCALES=["de", "fr"],
        STALE_TRANSLATION_THRESHOLD_DAYS=30,
    )
    def test_get_stale_docs_ai(self):
        """Test finding stale translations for AI flow (all AI docs + archived HYBRID docs)."""
        old_date = datetime.now() - timedelta(days=35)

        # Create stale translation in AI locale (non-archived)
        doc1_de = DocumentFactory(parent=self.doc1_en, locale="de")
        ApprovedRevisionFactory(
            document=doc1_de,
            based_on=self.rev1_en,
            created=old_date,
            reviewed=old_date,
        )

        # Create stale translation for archived doc in HYBRID locale
        doc2_es = DocumentFactory(parent=self.doc2_en, locale="es")
        ApprovedRevisionFactory(
            document=doc2_es,
            based_on=self.rev2_en,
            created=old_date,
            reviewed=old_date,
        )

        # Update English documents to make translations stale
        ApprovedRevisionFactory(
            document=self.doc1_en,
            created=datetime.now() - timedelta(days=1),
            reviewed=datetime.now() - timedelta(days=1),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        ApprovedRevisionFactory(
            document=self.doc2_en,
            created=datetime.now() - timedelta(days=1),
            reviewed=datetime.now() - timedelta(days=1),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )

        results = self.query_builder.get_stale_docs_ai(limit=10)

        # Should find both: AI locale (all docs) + HYBRID locale (archived only)
        self.assertEqual(len(results), 2)
        locales = {locale for _, _, locale in results}
        self.assertEqual(locales, {"de", "es"})

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es", "ro"],
        AI_ENABLED_LOCALES=["de", "fr"],
    )
    def test_get_missing_docs_hybrid(self):
        """Test finding missing translations in HYBRID locales (non-archived only)."""
        results = self.query_builder.get_missing_docs_hybrid(limit=10)

        # Should find non-archived docs without translations
        english_ids = {english_doc.id for english_doc, _, _ in results}
        self.assertIn(self.doc1_en.id, english_ids)
        self.assertIn(self.doc3_en.id, english_ids)
        self.assertNotIn(self.doc2_en.id, english_ids)  # Archived, excluded

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es", "ro"],
        AI_ENABLED_LOCALES=["de", "fr"],
    )
    def test_get_missing_docs_ai(self):
        """Test finding missing translations for AI flow (all AI + archived HYBRID)."""
        results = self.query_builder.get_missing_docs_ai(limit=10)

        # Should find: all docs for AI locales + archived docs for HYBRID locales
        results_by_locale = {}
        for english_doc, _, locale in results:
            if locale not in results_by_locale:
                results_by_locale[locale] = []
            results_by_locale[locale].append(english_doc.id)

        # AI locales should have all documents
        for ai_locale in ["de", "fr"]:
            self.assertIn(self.doc1_en.id, results_by_locale[ai_locale])
            self.assertIn(self.doc2_en.id, results_by_locale[ai_locale])
            self.assertIn(self.doc3_en.id, results_by_locale[ai_locale])

        # HYBRID locales should only have archived documents
        for hybrid_locale in ["es", "ro"]:
            self.assertIn(self.doc2_en.id, results_by_locale[hybrid_locale])
            self.assertNotIn(self.doc1_en.id, results_by_locale[hybrid_locale])
            self.assertNotIn(self.doc3_en.id, results_by_locale[hybrid_locale])

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es", "ro"],
        HYBRID_REVIEW_GRACE_PERIOD=72,
    )
    def test_get_pending_translations(self):
        """Test finding pending translations that exceeded grace period."""
        old_enough = datetime.now() - timedelta(hours=80)
        too_recent = datetime.now() - timedelta(hours=50)

        # Create pending translation that should be auto-approved
        doc1_es = DocumentFactory(parent=self.doc1_en, locale="es")
        rev_old = RevisionFactory(
            document=doc1_es,
            based_on=self.rev1_en,
            creator=self.sumo_bot,
            created=old_enough,
            reviewed=None,
            is_approved=False,
        )

        # Create pending translation that's too recent
        doc1_ro = DocumentFactory(parent=self.doc1_en, locale="ro")
        RevisionFactory(
            document=doc1_ro,
            based_on=self.rev1_en,
            creator=self.sumo_bot,
            created=too_recent,
            reviewed=None,
            is_approved=False,
        )

        results = self.query_builder.get_pending_translations()

        # Should only find the old one
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().id, rev_old.id)


class TranslationStrategyFactoryTests(TestCase):
    """Tests for TranslationStrategyFactory routing logic."""

    def setUp(self):
        self.factory = TranslationStrategyFactory()

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es", "ro"],
        AI_ENABLED_LOCALES=["de", "fr"],
    )
    def test_get_method_for_document_archived_hybrid(self):
        """Archived documents in HYBRID locales should use AI flow."""
        archived_doc = DocumentFactory(is_archived=True)

        method = self.factory.get_method_for_document(archived_doc, "es")

        self.assertEqual(method, TranslationMethod.AI)

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es", "ro"],
        AI_ENABLED_LOCALES=["de", "fr"],
    )
    def test_get_method_for_document_non_archived_hybrid(self):
        """Non-archived documents in HYBRID locales should use HYBRID flow."""
        active_doc = DocumentFactory(is_archived=False)

        method = self.factory.get_method_for_document(active_doc, "es")

        self.assertEqual(method, TranslationMethod.HYBRID)

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es", "ro"],
        AI_ENABLED_LOCALES=["de", "fr"],
    )
    def test_get_method_for_document_ai_locale(self):
        """Documents in AI locales always use AI flow regardless of archive status."""
        archived_doc = DocumentFactory(is_archived=True)
        active_doc = DocumentFactory(is_archived=False)

        self.assertEqual(self.factory.get_method_for_document(archived_doc, "de"), TranslationMethod.AI)
        self.assertEqual(self.factory.get_method_for_document(active_doc, "de"), TranslationMethod.AI)

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es", "ro"],
        AI_ENABLED_LOCALES=["de", "fr"],
    )
    def test_get_method_for_document_manual_locale(self):
        """Documents in manual locales use MANUAL flow."""
        doc = DocumentFactory(is_archived=False)

        method = self.factory.get_method_for_document(doc, "ja")

        self.assertEqual(method, TranslationMethod.MANUAL)


class StaleTranslationServiceTests(TestCase):
    """Tests for StaleTranslationService."""

    def setUp(self):
        self.service = StaleTranslationService()

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es"],
        AI_ENABLED_LOCALES=["de"],
        STALE_TRANSLATION_THRESHOLD_DAYS=30,
        STALE_TRANSLATION_BATCH_SIZE=10,
    )
    @patch("kitsune.wiki.services.TranslationStrategyFactory.execute")
    def test_process_stale_with_strategy_filter(self, mock_execute):
        """Test processing stale translations with strategy filter."""
        # Create stale translations
        old_date = datetime.now() - timedelta(days=35)

        doc_en = DocumentFactory(is_localizable=True, is_archived=False)
        rev_en = ApprovedRevisionFactory(
            document=doc_en,
            created=datetime(2024, 1, 1),
            reviewed=datetime(2024, 1, 2),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )

        # Create old translations
        doc_es = DocumentFactory(parent=doc_en, locale="es")
        ApprovedRevisionFactory(
            document=doc_es,
            based_on=rev_en,
            created=old_date,
            reviewed=old_date,
        )

        doc_de = DocumentFactory(parent=doc_en, locale="de")
        ApprovedRevisionFactory(
            document=doc_de,
            based_on=rev_en,
            created=old_date,
            reviewed=old_date,
        )

        # Update English to make translations stale
        ApprovedRevisionFactory(
            document=doc_en,
            created=datetime.now() - timedelta(days=1),
            reviewed=datetime.now() - timedelta(days=1),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )

        # Process only HYBRID strategy
        results = self.service.process_stale(limit=10, strategy=TranslationMethod.HYBRID)

        # Should only process HYBRID locale (es)
        self.assertEqual(len(results), 1)
        _, _, locale = results[0]
        self.assertEqual(locale, "es")
        self.assertEqual(mock_execute.call_count, 1)


class MissingTranslationServiceTests(TestCase):
    """Tests for MissingTranslationService."""

    def setUp(self):
        self.service = MissingTranslationService()

    @override_settings(
        HYBRID_ENABLED_LOCALES=["es", "ro"],
        AI_ENABLED_LOCALES=["de"],
        STALE_TRANSLATION_BATCH_SIZE=10,
    )
    @patch("kitsune.wiki.services.TranslationStrategyFactory.execute")
    def test_process_missing(self, mock_execute):
        """Test processing missing translations."""
        # Create English documents
        doc1_en = DocumentFactory(is_localizable=True, is_archived=False)
        ApprovedRevisionFactory(
            document=doc1_en,
            created=datetime(2024, 1, 1),
            reviewed=datetime(2024, 1, 2),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )

        doc2_en = DocumentFactory(is_localizable=True, is_archived=True)
        ApprovedRevisionFactory(
            document=doc2_en,
            created=datetime(2024, 1, 1),
            reviewed=datetime(2024, 1, 2),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )

        results = self.service.process_missing(limit=50)

        # Should create translations for:
        # - AI locale (de): both docs
        # - HYBRID locales (es, ro): only archived doc
        self.assertGreater(len(results), 0)
        self.assertGreater(mock_execute.call_count, 0)
