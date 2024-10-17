from datetime import datetime, timedelta
from unittest import mock

from kitsune.dashboards import LAST_30_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.l10n.tests import make_mt_config
from kitsune.l10n.utils import get_l10n_bot
from kitsune.l10n.wiki import create_machine_translations
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.config import (
    MAJOR_SIGNIFICANCE,
    MEDIUM_SIGNIFICANCE,
    TYPO_SIGNIFICANCE,
)
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DocumentFactory,
    RedirectRevisionFactory,
    RevisionFactory,
)


THIRTY_DAYS = timedelta(days=30)


class CreateMachineTranslationsTests(TestCase):

    def setUp(self):
        super().setUp()
        self.l10n_bot = get_l10n_bot()
        now = datetime.now()
        two_days_ago = now - timedelta(days=2)
        four_days_ago = now - timedelta(days=4)
        self.group1 = GroupFactory()
        self.group2 = GroupFactory()

        self.doc1_en = DocumentFactory(slug="doc1_slug")
        rev1_en = ApprovedRevisionFactory(
            document=self.doc1_en,
            created=datetime(2024, 5, 1),
            reviewed=datetime(2024, 5, 2),
            reviewer=UserFactory(),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        rev2_en = ApprovedRevisionFactory(
            document=self.doc1_en,
            created=datetime(2024, 5, 5),
            reviewed=datetime(2024, 5, 6),
            reviewer=UserFactory(),
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        rev2_en.reviewer.groups.add(GroupFactory())
        rev2_en.reviewer.groups.add(self.group1)
        rev3_en = ApprovedRevisionFactory(
            document=self.doc1_en,
            created=datetime(2024, 6, 7),
            reviewed=datetime(2024, 6, 8),
            reviewer=UserFactory(),
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
        doc1_fr = DocumentFactory(parent=self.doc1_en, locale="fr")
        ApprovedRevisionFactory(
            document=doc1_fr,
            based_on=rev1_en,
            created=datetime(2024, 5, 3),
            reviewed=datetime(2024, 5, 4),
        )
        doc1_el = DocumentFactory(parent=self.doc1_en, locale="el")
        RevisionFactory(
            document=doc1_el,
            based_on=rev3_en,
            created=datetime(2024, 7, 1),
            reviewed=None,
        )
        doc1_ja = DocumentFactory(parent=self.doc1_en, locale="ja")
        RevisionFactory(
            document=doc1_ja,
            based_on=rev3_en,
            created=datetime(2024, 7, 1),
            reviewed=None,
        )
        doc1_ro = DocumentFactory(parent=self.doc1_en, locale="ro")
        RevisionFactory(
            document=doc1_ro,
            based_on=rev3_en,
            created=two_days_ago,
            reviewed=None,
        )
        doc1_it = DocumentFactory(parent=self.doc1_en, locale="it")
        ApprovedRevisionFactory(
            document=doc1_it,
            based_on=rev1_en,
            created=datetime(2024, 5, 3),
            reviewed=datetime(2024, 5, 4),
        )
        RevisionFactory(
            document=doc1_it,
            based_on=rev2_en,
            created=four_days_ago,
            creator=self.l10n_bot,
            reviewed=None,
        )

        self.doc2_en = DocumentFactory(slug="doc2_slug")
        ApprovedRevisionFactory(
            document=self.doc2_en,
            created=datetime(2024, 5, 2),
            reviewed=datetime(2024, 5, 3),
            reviewer=UserFactory(),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        rev2_en_2 = ApprovedRevisionFactory(
            document=self.doc2_en,
            created=datetime(2024, 5, 6),
            reviewed=datetime(2024, 5, 7),
            reviewer=UserFactory(),
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        rev2_en_2.reviewer.groups.add(GroupFactory())
        rev2_en_2.reviewer.groups.add(self.group2)
        rev3_en_2 = ApprovedRevisionFactory(
            document=self.doc2_en,
            created=datetime(2024, 6, 7),
            reviewed=datetime(2024, 6, 8),
            reviewer=UserFactory(),
            significance=TYPO_SIGNIFICANCE,
            is_ready_for_localization=False,
        )

        doc2_es = DocumentFactory(parent=self.doc2_en, locale="es")
        ApprovedRevisionFactory(
            document=doc2_es,
            based_on=rev2_en_2,
            created=datetime(2024, 5, 7),
            reviewed=datetime(2024, 5, 8),
        )
        RevisionFactory(
            document=doc2_es,
            based_on=rev3_en_2,
            created=datetime(2024, 7, 1),
            reviewed=None,
        )
        doc2_el = DocumentFactory(parent=self.doc2_en, locale="el")
        RevisionFactory(
            document=doc2_el,
            based_on=rev3_en_2,
            created=four_days_ago,
            reviewed=None,
        )
        doc2_ro = DocumentFactory(parent=self.doc2_en, locale="ro")
        RevisionFactory(
            document=doc2_ro,
            based_on=rev2_en_2,
            created=two_days_ago,
            reviewed=None,
        )

        doc3_en = DocumentFactory(is_localizable=False)
        ApprovedRevisionFactory(
            document=doc3_en,
            created=datetime(2024, 5, 1),
            reviewed=datetime(2024, 5, 2),
            reviewer=UserFactory(),
            significance=MAJOR_SIGNIFICANCE,
        )

        doc4_en = DocumentFactory()
        rev1_en_4 = ApprovedRevisionFactory(
            document=doc4_en,
            created=datetime(2024, 5, 1),
            reviewed=datetime(2024, 5, 2),
            reviewer=UserFactory(),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        ApprovedRevisionFactory(
            document=doc4_en,
            created=datetime(2024, 5, 5),
            reviewed=datetime(2024, 5, 6),
            reviewer=UserFactory(),
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        ApprovedRevisionFactory(
            document=doc4_en,
            created=datetime(2024, 6, 7),
            reviewed=datetime(2024, 6, 8),
            reviewer=UserFactory(),
            significance=TYPO_SIGNIFICANCE,
            is_ready_for_localization=False,
        )

        doc4_it = DocumentFactory(parent=doc4_en, locale="it")
        ApprovedRevisionFactory(
            document=doc4_it,
            based_on=rev1_en_4,
            created=datetime(2024, 5, 3),
            reviewed=datetime(2024, 5, 4),
        )

        doc4_en.is_archived = True
        doc4_en.save()

        doc5_en = DocumentFactory()
        rev1_en_5 = ApprovedRevisionFactory(
            document=doc5_en,
            created=datetime(2024, 5, 1),
            reviewed=datetime(2024, 5, 2),
            reviewer=UserFactory(),
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        ApprovedRevisionFactory(
            document=doc5_en,
            created=datetime(2024, 5, 5),
            reviewed=datetime(2024, 5, 6),
            reviewer=UserFactory(),
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        ApprovedRevisionFactory(
            document=doc5_en,
            created=datetime(2024, 6, 7),
            reviewed=datetime(2024, 6, 8),
            reviewer=UserFactory(),
            significance=TYPO_SIGNIFICANCE,
            is_ready_for_localization=False,
        )

        doc5_ro = DocumentFactory(parent=doc5_en, locale="ro")
        ApprovedRevisionFactory(
            document=doc5_ro,
            based_on=rev1_en_5,
            created=datetime(2024, 5, 3),
            reviewed=datetime(2024, 5, 4),
        )

        RedirectRevisionFactory(document=doc5_en)

        WikiDocumentVisits.objects.create(document=self.doc1_en, visits=100, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc1_it, visits=18, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc1_el, visits=17, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc1_ro, visits=16, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc1_es, visits=15, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=self.doc2_en, visits=175, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc2_es, visits=12, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc2_el, visits=11, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc2_ro, visits=10, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc3_en, visits=50, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc4_en, visits=40, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc5_en, visits=30, period=LAST_30_DAYS)

    def assert_calls_for_doc1_only(self, create_machine_translation_mock, report):
        create_machine_translation_mock.assert_has_calls(
            [
                mock.call("test-model", self.doc1_en, "el", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
                mock.call("test-model", self.doc1_en, "es", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
                mock.call("test-model", self.doc1_en, "de", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
            ],
            any_order=False,
        )
        self.assertEqual(create_machine_translation_mock.call_count, 3)
        self.assertEqual(set(report.keys()), set(["el", "de", "es"]))
        self.assertIn("already_approved", report["el"])
        self.assertIn("already_approved", report["es"])
        self.assertIn("already_approved", report["de"])
        self.assertEqual(len(report["el"]["already_approved"]), 1)
        self.assertEqual(len(report["es"]["already_approved"]), 1)
        self.assertEqual(len(report["de"]["already_approved"]), 1)

    def assert_calls_for_doc2_only(self, create_machine_translation_mock, report):
        create_machine_translation_mock.assert_has_calls(
            [
                mock.call("test-model", self.doc2_en, "el", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
                mock.call("test-model", self.doc2_en, "de", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
                mock.call("test-model", self.doc2_en, "it", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
            ],
            any_order=False,
        )
        self.assertEqual(create_machine_translation_mock.call_count, 3)
        self.assertEqual(set(report.keys()), set(["el", "de", "it"]))
        self.assertIn("already_approved", report["el"])
        self.assertIn("already_approved", report["de"])
        self.assertIn("already_approved", report["it"])
        self.assertEqual(len(report["el"]["already_approved"]), 1)
        self.assertEqual(len(report["de"]["already_approved"]), 1)
        self.assertEqual(len(report["it"]["already_approved"]), 1)

    def assert_calls_for_doc1_and_doc2(self, create_machine_translation_mock, report):
        create_machine_translation_mock.assert_has_calls(
            [
                mock.call("test-model", self.doc2_en, "el", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
                mock.call("test-model", self.doc1_en, "el", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
                mock.call("test-model", self.doc1_en, "es", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
                mock.call("test-model", self.doc2_en, "de", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
                mock.call("test-model", self.doc2_en, "it", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
                mock.call("test-model", self.doc1_en, "de", self.l10n_bot, THIRTY_DAYS),
                mock.call().is_approved.__bool__(),
                mock.call().get_absolute_url(),
            ],
            any_order=False,
        )
        self.assertEqual(create_machine_translation_mock.call_count, 6)
        self.assertEqual(set(report.keys()), set(["el", "es", "de", "it"]))
        self.assertIn("already_approved", report["el"])
        self.assertIn("already_approved", report["es"])
        self.assertIn("already_approved", report["de"])
        self.assertIn("already_approved", report["it"])
        self.assertEqual(len(report["el"]["already_approved"]), 2)
        self.assertEqual(len(report["es"]["already_approved"]), 1)
        self.assertEqual(len(report["de"]["already_approved"]), 2)
        self.assertEqual(len(report["it"]["already_approved"]), 1)

    @mock.patch("kitsune.l10n.wiki.create_machine_translation")
    def test_create_machine_translations_without_default_document(
        self, create_machine_translation_mock
    ):
        mt_config = make_mt_config(
            review_grace_period=timedelta(days=3),
            post_review_grace_period=timedelta(days=5),
            enabled_languages=["el", "ro", "es", "it", "de"],
        )
        report = create_machine_translations(mt_config)
        self.assert_calls_for_doc1_and_doc2(create_machine_translation_mock, report)

    @mock.patch("kitsune.l10n.wiki.create_machine_translation")
    def test_create_machine_translations_with_default_document(
        self, create_machine_translation_mock
    ):
        mt_config = make_mt_config(
            review_grace_period=timedelta(days=3),
            post_review_grace_period=timedelta(days=5),
            enabled_languages=["el", "ro", "es", "it", "de"],
        )

        with self.subTest("doc1 as default doc argument"):
            report = create_machine_translations(mt_config, self.doc1_en)
            self.assert_calls_for_doc1_only(create_machine_translation_mock, report)

        create_machine_translation_mock.reset_mock()

        with self.subTest("doc2 as default doc argument"):
            report = create_machine_translations(mt_config, self.doc2_en)
            self.assert_calls_for_doc2_only(create_machine_translation_mock, report)

    @mock.patch("kitsune.l10n.wiki.create_machine_translation")
    def test_create_machine_translations_with_slug_filtering(
        self, create_machine_translation_mock
    ):
        with self.subTest("case 1"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_slugs=["doc1*", "doc2_slug"],
                disabled_slugs=["doc*"],
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            create_machine_translation_mock.assert_not_called()
            self.assertFalse(report)

        with self.subTest("case 2"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                disabled_slugs=["doc1*", "doc2_slug"],
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            create_machine_translation_mock.assert_not_called()
            self.assertFalse(report)

        with self.subTest("case 3"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_slugs=["xyz"],
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            create_machine_translation_mock.assert_not_called()
            self.assertFalse(report)

        with self.subTest("case 4"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_slugs=["doc1_slug"],
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config, self.doc2_en)
            create_machine_translation_mock.assert_not_called()
            self.assertFalse(report)

        with self.subTest("case 5"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_slugs=["doc2*", "xyz"],
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config, self.doc1_en)
            create_machine_translation_mock.assert_not_called()
            self.assertFalse(report)

        with self.subTest("case 6"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_slugs=["doc2*", "xyz"],
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config, self.doc2_en)
            self.assert_calls_for_doc2_only(create_machine_translation_mock, report)

        with self.subTest("case 7"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                disabled_slugs=["doc1*"],
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            self.assert_calls_for_doc2_only(create_machine_translation_mock, report)

        with self.subTest("case 8"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_slugs=["doc2*"],
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            self.assert_calls_for_doc2_only(create_machine_translation_mock, report)

        with self.subTest("case 9"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_slugs=["doc2*", "doc1_slug"],
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            self.assert_calls_for_doc1_and_doc2(create_machine_translation_mock, report)

    @mock.patch("kitsune.l10n.wiki.create_machine_translation")
    def test_create_machine_translations_with_approved_date_filtering(
        self, create_machine_translation_mock
    ):
        with self.subTest("case 1"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approved_after=datetime(2024, 5, 7),
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            create_machine_translation_mock.assert_not_called()
            self.assertFalse(report)

        with self.subTest("case 2"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_slugs=["doc2_slug"],
                limit_to_approved_after=datetime(2024, 5, 5),
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            self.assert_calls_for_doc2_only(create_machine_translation_mock, report)

        with self.subTest("case 3"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approved_after=datetime(2024, 5, 6),
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            self.assert_calls_for_doc2_only(create_machine_translation_mock, report)

        with self.subTest("case 4"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approved_after=datetime(2024, 5, 5),
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            self.assert_calls_for_doc1_and_doc2(create_machine_translation_mock, report)

        with self.subTest("case 5"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approved_after=datetime(2024, 5, 5),
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config, self.doc2_en)
            self.assert_calls_for_doc2_only(create_machine_translation_mock, report)

        with self.subTest("case 6"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approved_after=datetime(2024, 5, 5),
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config, self.doc1_en)
            self.assert_calls_for_doc1_only(create_machine_translation_mock, report)

        with self.subTest("case 7"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approved_after=datetime(2024, 5, 6),
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config, self.doc1_en)
            create_machine_translation_mock.assert_not_called()
            self.assertFalse(report)

    @mock.patch("kitsune.l10n.wiki.create_machine_translation")
    def test_create_machine_translations_with_approver_filtering(
        self, create_machine_translation_mock
    ):
        with self.subTest("case 1"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approver_in_group=GroupFactory(),
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            create_machine_translation_mock.assert_not_called()
            self.assertFalse(report)

        with self.subTest("case 2"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approver_in_group=self.group1,
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config, self.doc2_en)
            create_machine_translation_mock.assert_not_called()
            self.assertFalse(report)

        with self.subTest("case 3"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approver_in_group=self.group2,
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config, self.doc1_en)
            create_machine_translation_mock.assert_not_called()
            self.assertFalse(report)

        with self.subTest("case 4"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approver_in_group=self.group1,
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config, self.doc1_en)
            self.assert_calls_for_doc1_only(create_machine_translation_mock, report)

        with self.subTest("case 5"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approver_in_group=self.group2,
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config, self.doc2_en)
            self.assert_calls_for_doc2_only(create_machine_translation_mock, report)

        with self.subTest("case 6"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approver_in_group=self.group1,
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            self.assert_calls_for_doc1_only(create_machine_translation_mock, report)

        with self.subTest("case 7"):
            mt_config = make_mt_config(
                review_grace_period=timedelta(days=3),
                post_review_grace_period=timedelta(days=5),
                enabled_languages=["el", "ro", "es", "it", "de"],
                limit_to_approver_in_group=self.group2,
            )
            create_machine_translation_mock.reset_mock()
            report = create_machine_translations(mt_config)
            self.assert_calls_for_doc2_only(create_machine_translation_mock, report)
