from datetime import datetime, timedelta

from django.test import TestCase
from django.test.utils import override_settings

from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory
from kitsune.wiki.config import MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE, TYPO_SIGNIFICANCE
from kitsune.wiki.services import HybridTranslationService
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory, RevisionFactory

APPROVED_MSG = "Automatically approved because it was not reviewed within 72 hour(s)."
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

        datetime_prior_to_test = datetime.now()

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

        datetime_prior_to_test = datetime.now()

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

        datetime_prior_to_test = datetime.now()

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

        datetime_prior_to_test = datetime.now()

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
