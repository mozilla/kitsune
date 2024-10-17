from datetime import datetime, timedelta

from kitsune.l10n.tests import make_mt_config
from kitsune.l10n.utils import get_l10n_bot
from kitsune.l10n.wiki import manage_existing_machine_translations
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.config import (
    MAJOR_SIGNIFICANCE,
    MEDIUM_SIGNIFICANCE,
    TYPO_SIGNIFICANCE,
)
from kitsune.wiki.models import Revision
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DocumentFactory,
    RedirectRevisionFactory,
    RevisionFactory,
)


APPROVED_MSG = "Automatically approved because it was not reviewed within 3 days."
REJECTED_MSG = "No longer relevant."
APPROVED_COPY_MSG = (
    "Automatically created and approved because an alternate translation "
    "was not approved within 5 days after the rejection of %(url)s."
)


class ManageExistingMachineTranslationsTests(TestCase):

    def setUp(self):
        super().setUp()
        self.l10n_bot = get_l10n_bot()
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
            creator=self.l10n_bot,
            created=two_days_ago,
            reviewed=None,
        )

        doc1_ro = DocumentFactory(parent=self.doc1_en, locale="ro")
        self.rev1_ro = RevisionFactory(
            document=doc1_ro,
            based_on=rev2_en,
            creator=self.l10n_bot,
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
            creator=self.l10n_bot,
            created=datetime(2024, 5, 3),
            reviewed=None,
        )
        self.rev2_el = RevisionFactory(
            document=self.doc1_el,
            based_on=rev2_en,
            creator=self.l10n_bot,
            created=four_days_ago,
            reviewed=None,
        )

        self.doc1_ja = DocumentFactory(parent=self.doc1_en, locale="ja")
        self.rev1_ja = RevisionFactory(
            document=self.doc1_ja,
            based_on=rev1_en,
            creator=self.l10n_bot,
            created=datetime(2024, 5, 3),
            reviewed=None,
        )
        self.rev2_ja = RevisionFactory(
            document=self.doc1_ja,
            based_on=rev2_en,
            creator=self.l10n_bot,
            created=four_days_ago,
            reviewed=None,
        )

        doc1_it = DocumentFactory(parent=self.doc1_en, locale="it")
        self.rev1_it = RevisionFactory(
            document=doc1_it,
            based_on=rev2_en,
            creator=self.l10n_bot,
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
            creator=self.l10n_bot,
            created=two_days_ago,
            reviewed=None,
        )

        doc2_ro = DocumentFactory(parent=self.doc2_en, locale="ro")
        self.rev1_ro_2 = RevisionFactory(
            document=doc2_ro,
            based_on=rev2_en_2,
            creator=self.l10n_bot,
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
            creator=self.l10n_bot,
            created=datetime(2024, 5, 3),
            reviewed=None,
        )
        self.rev2_el_2 = RevisionFactory(
            document=doc2_el,
            based_on=rev2_en_2,
            creator=self.l10n_bot,
            created=four_days_ago,
            reviewed=None,
        )

        doc2_ja = DocumentFactory(parent=self.doc2_en, locale="ja")
        self.rev1_ja_2 = RevisionFactory(
            document=doc2_ja,
            based_on=rev1_en_2,
            creator=self.l10n_bot,
            created=datetime(2024, 5, 3),
            reviewed=None,
        )
        self.rev2_ja_2 = RevisionFactory(
            document=doc2_ja,
            based_on=rev2_en_2,
            creator=self.l10n_bot,
            created=four_days_ago,
            reviewed=None,
        )

        doc2_it = DocumentFactory(parent=self.doc2_en, locale="it")
        self.rev1_it_2 = RevisionFactory(
            document=doc2_it,
            based_on=rev2_en_2,
            creator=self.l10n_bot,
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

    def test_manage_existing_machine_translations_with_no_argument(self):
        mt_config = make_mt_config(
            review_grace_period=timedelta(days=3),
            post_review_grace_period=timedelta(days=5),
            enabled_languages=["el", "ro", "es", "it", "de"],
        )

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

        report = manage_existing_machine_translations(mt_config)

        for rev in revs:
            rev.refresh_from_db()

        # The Japanese locale is included in the report because it had machine
        # translations that required management, and all existing machine
        # translations are managed even if they're within locales that are no
        # longer enabled.
        self.assertEqual(set(report.keys()), set(["el", "ro", "it", "ja"]))
        self.assertEqual(
            set(report["el"].keys()),
            set(["rejections", "pre_review_approvals"]),
        )
        self.assertEqual(
            set(report["el"]["rejections"]),
            set([self.rev1_el.get_absolute_url(), self.rev1_el_2.get_absolute_url()]),
        )
        self.assertEqual(
            set(report["el"]["pre_review_approvals"]),
            set([self.rev2_el.get_absolute_url(), self.rev2_el_2.get_absolute_url()]),
        )
        self.assertEqual(
            set(report["ja"].keys()),
            set(["rejections", "pre_review_approvals"]),
        )
        self.assertEqual(
            set(report["ja"]["rejections"]),
            set([self.rev1_ja.get_absolute_url(), self.rev1_ja_2.get_absolute_url()]),
        )
        self.assertEqual(
            set(report["ja"]["pre_review_approvals"]),
            set([self.rev2_ja.get_absolute_url(), self.rev2_ja_2.get_absolute_url()]),
        )
        # The first Greek and Japanese revisions have been rejected because they're out-of-date.
        for rev in (self.rev1_el, self.rev1_el_2, self.rev1_ja, self.rev1_ja_2):
            self.assertFalse(rev.is_approved)
            self.assertTrue(rev.reviewed > datetime_prior_to_test)
            self.assertEqual(rev.reviewer, self.l10n_bot)
            self.assertEqual(rev.comment, REJECTED_MSG)

        # The second Greek and Japanese revisions have been approved because they're up-to-date
        # and the review grace period has expired.
        for rev in (self.rev2_el, self.rev2_el_2, self.rev2_ja, self.rev2_ja_2):
            self.assertTrue(rev.is_approved)
            self.assertTrue(rev.reviewed > datetime_prior_to_test)
            self.assertEqual(rev.reviewer, self.l10n_bot)
            self.assertEqual(rev.comment, APPROVED_MSG)

        # The second Spanish revision remains untouched because its review grace
        # period has not yet expired.
        for rev in (self.rev2_es, self.rev2_es_2):
            self.assertIsNone(rev.reviewed)
            self.assertFalse(rev.is_approved)

        self.assertEqual(list(report["ro"].keys()), ["rejections"])
        self.assertEqual(
            set(report["ro"]["rejections"]),
            set([self.rev1_ro.get_absolute_url(), self.rev1_ro_2.get_absolute_url()]),
        )

        # The first Romanian revision has been rejected because it was superseded
        # within its review grace period.
        for rev in (self.rev1_ro, self.rev1_ro_2):
            self.assertFalse(rev.is_approved)
            self.assertTrue(rev.reviewed > datetime_prior_to_test)
            self.assertEqual(rev.reviewer, self.l10n_bot)
            self.assertEqual(rev.comment, REJECTED_MSG)

        self.assertEqual(list(report["it"].keys()), ["post_rejection_approvals"])
        self.assertEqual(len(report["it"]["post_rejection_approvals"]), 2)

        # The first Italian revision was rejected, but an alternate revision wasn't
        # approved within the post-review grace period, so a copy of it should have
        # been created and approved by the L10n bot.
        for rev in (self.rev1_it, self.rev1_it_2):
            self.assertFalse(rev.is_approved)
            self.assertTrue(rev.reviewed)
            self.assertTrue(
                Revision.objects.filter(
                    is_approved=True,
                    creator=self.l10n_bot,
                    reviewer=self.l10n_bot,
                    created__gte=datetime_prior_to_test,
                    reviewed__gte=datetime_prior_to_test,
                    based_on=rev.based_on,
                    document=rev.document,
                    content=rev.content,
                    keywords=rev.keywords,
                    comment=APPROVED_COPY_MSG % dict(url=rev.get_absolute_url()),
                ).exists()
            )

    def test_manage_existing_machine_translations_with_default_doc1(self):
        mt_config = make_mt_config(
            review_grace_period=timedelta(days=3),
            post_review_grace_period=timedelta(days=5),
            enabled_languages=["el", "ro", "es", "it", "de"],
        )

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

        report = manage_existing_machine_translations(mt_config, self.doc1_en)

        for rev in revs:
            rev.refresh_from_db()

        # The Japanese locale is included in the report because it had machine
        # translations that required management, and all existing machine
        # translations are managed even if they're within locales that are no
        # longer enabled.
        self.assertEqual(set(report.keys()), set(["el", "ro", "it", "ja"]))

        self.assertEqual(
            set(report["el"].keys()),
            set(["rejections", "pre_review_approvals"]),
        )
        self.assertEqual(report["el"]["rejections"], [self.rev1_el.get_absolute_url()])
        self.assertEqual(report["el"]["pre_review_approvals"], [self.rev2_el.get_absolute_url()])
        self.assertEqual(
            set(report["ja"].keys()),
            set(["rejections", "pre_review_approvals"]),
        )
        self.assertEqual(report["ja"]["rejections"], [self.rev1_ja.get_absolute_url()])
        self.assertEqual(report["ja"]["pre_review_approvals"], [self.rev2_ja.get_absolute_url()])

        # The first Greek and Japanese revisions have been rejected because they're out-of-date,
        # but only the revision within the context of "doc1_en".
        self.assertFalse(self.rev1_el.is_approved)
        self.assertTrue(self.rev1_el.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_el.reviewer, self.l10n_bot)
        self.assertEqual(self.rev1_el.comment, REJECTED_MSG)
        self.assertFalse(self.rev1_el_2.is_approved)
        self.assertIsNone(self.rev1_el_2.reviewed)
        self.assertFalse(self.rev1_ja.is_approved)
        self.assertTrue(self.rev1_ja.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_ja.reviewer, self.l10n_bot)
        self.assertEqual(self.rev1_ja.comment, REJECTED_MSG)
        self.assertFalse(self.rev1_ja_2.is_approved)
        self.assertIsNone(self.rev1_ja_2.reviewed)

        # The second Greek and Japanese revisions have been approved because they're up-to-date
        # and the review grace period has expired, but only the revision within
        # the context of "doc1_en".
        self.assertTrue(self.rev2_el.is_approved)
        self.assertTrue(self.rev2_el.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev2_el.reviewer, self.l10n_bot)
        self.assertEqual(self.rev2_el.comment, APPROVED_MSG)
        self.assertFalse(self.rev2_el_2.is_approved)
        self.assertIsNone(self.rev2_el_2.reviewed)
        self.assertTrue(self.rev2_ja.is_approved)
        self.assertTrue(self.rev2_ja.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev2_ja.reviewer, self.l10n_bot)
        self.assertEqual(self.rev2_ja.comment, APPROVED_MSG)
        self.assertFalse(self.rev2_ja_2.is_approved)
        self.assertIsNone(self.rev2_ja_2.reviewed)

        # The second Spanish revision remains untouched because its review grace
        # period has not yet expired. That's true for the revision within the
        # context of "doc1_en", but the revision within the context of "doc2_en"
        # remains untouched because its out of context.
        for rev in (self.rev2_es, self.rev2_es_2):
            self.assertIsNone(rev.reviewed)
            self.assertFalse(rev.is_approved)

        self.assertEqual(list(report["ro"].keys()), ["rejections"])
        self.assertEqual(report["ro"]["rejections"], [self.rev1_ro.get_absolute_url()])

        # The first Romanian revision has been rejected because it was superseded
        # within its review grace period, but only the revision within the context
        # of "doc1_en".
        self.assertFalse(self.rev1_ro.is_approved)
        self.assertTrue(self.rev1_ro.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_ro.reviewer, self.l10n_bot)
        self.assertEqual(self.rev1_ro.comment, REJECTED_MSG)
        self.assertFalse(self.rev1_ro_2.is_approved)
        self.assertIsNone(self.rev1_ro_2.reviewed)

        self.assertEqual(list(report["it"].keys()), ["post_rejection_approvals"])
        self.assertEqual(len(report["it"]["post_rejection_approvals"]), 1)

        # The first Italian revision was rejected, but an alternate revision wasn't
        # approved within the post-review grace period, so a copy of it should have
        # been created and approved by the L10n bot. This only applies to the revision
        # within the context of "doc1_en".
        self.assertFalse(self.rev1_it.is_approved)
        self.assertTrue(self.rev1_it.reviewed)
        self.assertTrue(
            Revision.objects.filter(
                is_approved=True,
                creator=self.l10n_bot,
                reviewer=self.l10n_bot,
                created__gte=datetime_prior_to_test,
                reviewed__gte=datetime_prior_to_test,
                based_on=self.rev1_it.based_on,
                document=self.rev1_it.document,
                content=self.rev1_it.content,
                keywords=self.rev1_it.keywords,
                comment=APPROVED_COPY_MSG % dict(url=self.rev1_it.get_absolute_url()),
            ).exists()
        )
        self.assertFalse(self.rev1_it_2.is_approved)
        self.assertTrue(self.rev1_it_2.reviewed)
        self.assertFalse(
            Revision.objects.filter(
                is_approved=True,
                creator=self.l10n_bot,
                reviewer=self.l10n_bot,
                created__gte=datetime_prior_to_test,
                reviewed__gte=datetime_prior_to_test,
                based_on=self.rev1_it_2.based_on,
                document=self.rev1_it_2.document,
                content=self.rev1_it_2.content,
                keywords=self.rev1_it_2.keywords,
                comment=APPROVED_COPY_MSG % dict(url=self.rev1_it_2.get_absolute_url()),
            ).exists()
        )

    def test_manage_existing_machine_translations_with_default_doc2(self):
        mt_config = make_mt_config(
            review_grace_period=timedelta(days=3),
            post_review_grace_period=timedelta(days=5),
            enabled_languages=["el", "ro", "es", "it", "de"],
        )

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

        report = manage_existing_machine_translations(mt_config, self.doc2_en)

        for rev in revs:
            rev.refresh_from_db()

        # The Japanese locale is included in the report because it had machine
        # translations that required management, and all existing machine
        # translations are managed even if they're within locales that are no
        # longer enabled.
        self.assertEqual(set(report.keys()), set(["el", "ro", "it", "ja"]))

        self.assertEqual(
            set(report["el"].keys()),
            set(["rejections", "pre_review_approvals"]),
        )
        self.assertEqual(report["el"]["rejections"], [self.rev1_el_2.get_absolute_url()])
        self.assertEqual(report["el"]["pre_review_approvals"], [self.rev2_el_2.get_absolute_url()])
        self.assertEqual(
            set(report["ja"].keys()),
            set(["rejections", "pre_review_approvals"]),
        )
        self.assertEqual(report["ja"]["rejections"], [self.rev1_ja_2.get_absolute_url()])
        self.assertEqual(report["ja"]["pre_review_approvals"], [self.rev2_ja_2.get_absolute_url()])

        # The first Greek and Japanese revisions have been rejected because they're
        # out-of-date, but only the revision within the context of "doc2_en".
        self.assertFalse(self.rev1_el_2.is_approved)
        self.assertTrue(self.rev1_el_2.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_el_2.reviewer, self.l10n_bot)
        self.assertEqual(self.rev1_el_2.comment, REJECTED_MSG)
        self.assertFalse(self.rev1_el.is_approved)
        self.assertIsNone(self.rev1_el.reviewed)
        self.assertFalse(self.rev1_ja_2.is_approved)
        self.assertTrue(self.rev1_ja_2.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_ja_2.reviewer, self.l10n_bot)
        self.assertEqual(self.rev1_ja_2.comment, REJECTED_MSG)
        self.assertFalse(self.rev1_ja.is_approved)
        self.assertIsNone(self.rev1_ja.reviewed)

        # The second Greek and Japanese revisions have been approved because they're
        # up-to-date and the review grace period has expired, but only the revision
        # within the context of "doc2_en".
        self.assertTrue(self.rev2_el_2.is_approved)
        self.assertTrue(self.rev2_el_2.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev2_el_2.reviewer, self.l10n_bot)
        self.assertEqual(self.rev2_el_2.comment, APPROVED_MSG)
        self.assertFalse(self.rev2_el.is_approved)
        self.assertIsNone(self.rev2_el.reviewed)
        self.assertTrue(self.rev2_ja_2.is_approved)
        self.assertTrue(self.rev2_ja_2.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev2_ja_2.reviewer, self.l10n_bot)
        self.assertEqual(self.rev2_ja_2.comment, APPROVED_MSG)
        self.assertFalse(self.rev2_ja.is_approved)
        self.assertIsNone(self.rev2_ja.reviewed)

        # The second Spanish revision remains untouched because its review grace
        # period has not yet expired. That's true for the revision within the
        # context of "doc2_en", but the revision within the context of "doc1_en"
        # remains untouched because its out of context.
        for rev in (self.rev2_es, self.rev2_es_2):
            self.assertIsNone(rev.reviewed)
            self.assertFalse(rev.is_approved)

        self.assertEqual(list(report["ro"].keys()), ["rejections"])
        self.assertEqual(report["ro"]["rejections"], [self.rev1_ro_2.get_absolute_url()])

        # The first Romanian revision has been rejected because it was superseded
        # within its review grace period, but only the revision within the context
        # of "doc2_en".
        self.assertFalse(self.rev1_ro_2.is_approved)
        self.assertTrue(self.rev1_ro_2.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_ro_2.reviewer, self.l10n_bot)
        self.assertEqual(self.rev1_ro_2.comment, REJECTED_MSG)
        self.assertFalse(self.rev1_ro.is_approved)
        self.assertIsNone(self.rev1_ro.reviewed)

        self.assertEqual(list(report["it"].keys()), ["post_rejection_approvals"])
        self.assertEqual(len(report["it"]["post_rejection_approvals"]), 1)

        # The first Italian revision was rejected, but an alternate revision wasn't
        # approved within the post-review grace period, so a copy of it should have
        # been created and approved by the L10n bot. This only applies to the revision
        # within the context of "doc1_en".
        self.assertFalse(self.rev1_it_2.is_approved)
        self.assertTrue(self.rev1_it_2.reviewed)
        self.assertTrue(
            Revision.objects.filter(
                is_approved=True,
                creator=self.l10n_bot,
                reviewer=self.l10n_bot,
                created__gte=datetime_prior_to_test,
                reviewed__gte=datetime_prior_to_test,
                based_on=self.rev1_it_2.based_on,
                document=self.rev1_it_2.document,
                content=self.rev1_it_2.content,
                keywords=self.rev1_it_2.keywords,
                comment=APPROVED_COPY_MSG % dict(url=self.rev1_it_2.get_absolute_url()),
            ).exists()
        )
        self.assertFalse(self.rev1_it.is_approved)
        self.assertTrue(self.rev1_it.reviewed)
        self.assertFalse(
            Revision.objects.filter(
                is_approved=True,
                creator=self.l10n_bot,
                reviewer=self.l10n_bot,
                created__gte=datetime_prior_to_test,
                reviewed__gte=datetime_prior_to_test,
                based_on=self.rev1_it.based_on,
                document=self.rev1_it.document,
                content=self.rev1_it.content,
                keywords=self.rev1_it.keywords,
                comment=APPROVED_COPY_MSG % dict(url=self.rev1_it.get_absolute_url()),
            ).exists()
        )

    def test_manage_existing_machine_translations_with_doc1_el(self):
        mt_config = make_mt_config(
            review_grace_period=timedelta(days=3),
            post_review_grace_period=timedelta(days=5),
            enabled_languages=["el", "ro", "es", "it", "de"],
        )

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

        report = manage_existing_machine_translations(mt_config, self.doc1_el)

        for rev in revs:
            rev.refresh_from_db()

        self.assertEqual(list(report.keys()), ["el"])

        self.assertEqual(
            set(report["el"].keys()),
            set(["rejections", "pre_review_approvals"]),
        )
        self.assertEqual(report["el"]["rejections"], [self.rev1_el.get_absolute_url()])
        self.assertEqual(report["el"]["pre_review_approvals"], [self.rev2_el.get_absolute_url()])

        # The first Greek revision has been rejected because it's out-of-date,
        # but only the revision within the context of "doc1_el".
        self.assertFalse(self.rev1_el.is_approved)
        self.assertTrue(self.rev1_el.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev1_el.reviewer, self.l10n_bot)
        self.assertEqual(self.rev1_el.comment, REJECTED_MSG)

        # The second Greek revision has been approved because it's up-to-date
        # and the review grace period has expired, but only the revision within
        # the context of "doc1_el".
        self.assertTrue(self.rev2_el.is_approved)
        self.assertTrue(self.rev2_el.reviewed > datetime_prior_to_test)
        self.assertEqual(self.rev2_el.reviewer, self.l10n_bot)
        self.assertEqual(self.rev2_el.comment, APPROVED_MSG)

        for rev in revs:
            if rev in (self.rev1_el, self.rev2_el):
                continue
            self.assertFalse(rev.is_approved)
            if rev in (self.rev1_it, self.rev1_it_2):
                self.assertTrue(rev.reviewed)
                self.assertFalse(
                    Revision.objects.filter(
                        is_approved=True,
                        creator=self.l10n_bot,
                        reviewer=self.l10n_bot,
                        created__gte=datetime_prior_to_test,
                        reviewed__gte=datetime_prior_to_test,
                        based_on=rev.based_on,
                        document=rev.document,
                        content=rev.content,
                        keywords=rev.keywords,
                        comment=APPROVED_COPY_MSG % dict(url=rev.get_absolute_url()),
                    ).exists()
                )
            else:
                self.assertIsNone(rev.reviewed)

    def test_manage_existing_machine_translations_with_unready_document(self):
        mt_config = make_mt_config(
            enabled_languages=["el", "ro", "es", "it", "de"],
        )
        # The document has no current revision.
        doc = DocumentFactory()
        self.assertFalse(manage_existing_machine_translations(mt_config, doc))

        # The document has no latest_localizable_revision.
        ApprovedRevisionFactory(document=doc, is_ready_for_localization=False)
        self.assertFalse(manage_existing_machine_translations(mt_config, doc))

        # The document is a redirect.
        doc = RedirectRevisionFactory().document
        self.assertFalse(manage_existing_machine_translations(mt_config, doc))
