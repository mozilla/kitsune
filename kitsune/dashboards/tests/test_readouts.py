from datetime import datetime

from django.conf import settings

from kitsune.dashboards import LAST_30_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.dashboards.readouts import (
    AdministrationReadout,
    CannedResponsesReadout,
    HowToContributeReadout,
    MostVisitedDefaultLanguageReadout,
    MostVisitedTranslationsReadout,
    NeedsChangesReadout,
    TemplateReadout,
    TemplateTranslationsReadout,
    UnreadyForLocalizationReadout,
    UnreviewedReadout,
    kb_overview_rows,
    l10n_overview_rows,
)
from kitsune.products.tests import ProductFactory
from kitsune.sumo.models import ModelBase
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory, add_permission
from kitsune.wiki.config import (
    ADMINISTRATION_CATEGORY,
    CANNED_RESPONSES_CATEGORY,
    CATEGORIES,
    HOW_TO_CONTRIBUTE_CATEGORY,
    MAJOR_SIGNIFICANCE,
    MEDIUM_SIGNIFICANCE,
    TEMPLATES_CATEGORY,
    TYPO_SIGNIFICANCE,
)
from kitsune.wiki.models import Revision
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DocumentFactory,
    RedirectRevisionFactory,
    RevisionFactory,
    TemplateDocumentFactory,
    TranslatedRevisionFactory,
)


class MockRequest(object):
    LANGUAGE_CODE = "de"  # Same locale as translated_revision uses by default


class ReadoutTestCase(TestCase):
    """Test case for one readout. Provides some convenience methods."""

    def rows(self, locale=None, product=None, user=None):
        """Return the rows show by the readout this class tests."""
        request = MockRequest()
        if user:
            request.user = user
        return self.readout(request, locale=locale, product=product).rows()

    def row(self, locale=None, product=None, user=None):
        """Return first row shown by the readout this class tests."""
        return self.rows(locale=locale, product=product, user=user)[0]

    def titles(self, locale=None, product=None):
        """Return the titles shown by the Unreviewed Changes readout."""
        return [
            row["title"]
            for row in self.readout(MockRequest(), locale=locale, product=product).rows()
        ]


class KBOverviewTests(TestCase):
    def test_unapproved_articles(self):
        self.assertEqual(0, len(kb_overview_rows()))
        RevisionFactory()
        self.assertEqual(0, len(kb_overview_rows()))
        ApprovedRevisionFactory()
        self.assertEqual(1, len(kb_overview_rows()))
        group1 = GroupFactory(name="group1")
        ApprovedRevisionFactory(document__restrict_to_groups=[group1])
        self.assertEqual(1, len(kb_overview_rows()))
        user1 = UserFactory(groups=[group1])
        self.assertEqual(2, len(kb_overview_rows(user=user1)))

    def test_ready_for_l10n(self):
        d1 = DocumentFactory()
        ApprovedRevisionFactory(document=d1, significance=MAJOR_SIGNIFICANCE)
        d2 = DocumentFactory()
        rev1_d2 = RevisionFactory(document=d2, significance=None)

        WikiDocumentVisits.objects.create(document=d1, visits=20, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=d2, visits=10, period=LAST_30_DAYS)

        data = kb_overview_rows(user=UserFactory(is_staff=True, is_superuser=True))
        self.assertEqual(2, len(data))
        self.assertEqual(False, data[0]["ready_for_l10n"])
        self.assertEqual(False, data[1]["ready_for_l10n"])

        ApprovedRevisionFactory(
            document=d1, is_ready_for_localization=True, significance=MEDIUM_SIGNIFICANCE
        )
        rev1_d2.is_approved = True
        rev1_d2.significance = MAJOR_SIGNIFICANCE
        rev1_d2.save()
        data = kb_overview_rows()
        self.assertEqual(True, data[0]["ready_for_l10n"])
        self.assertEqual(False, data[1]["ready_for_l10n"])

        ApprovedRevisionFactory(document=d1, significance=TYPO_SIGNIFICANCE)
        ApprovedRevisionFactory(
            document=d2, is_ready_for_localization=True, significance=MEDIUM_SIGNIFICANCE
        )
        data = kb_overview_rows()
        self.assertEqual(True, data[0]["ready_for_l10n"])
        self.assertEqual(True, data[1]["ready_for_l10n"])

        ApprovedRevisionFactory(document=d1, significance=MEDIUM_SIGNIFICANCE)
        ApprovedRevisionFactory(document=d2, significance=TYPO_SIGNIFICANCE)
        data = kb_overview_rows()
        self.assertEqual(False, data[0]["ready_for_l10n"])
        self.assertEqual(True, data[1]["ready_for_l10n"])

        ApprovedRevisionFactory(
            document=d1, is_ready_for_localization=True, significance=MAJOR_SIGNIFICANCE
        )
        ApprovedRevisionFactory(document=d2, significance=MAJOR_SIGNIFICANCE)
        data = kb_overview_rows()
        self.assertEqual(True, data[0]["ready_for_l10n"])
        self.assertEqual(False, data[1]["ready_for_l10n"])

        ApprovedRevisionFactory(document=d1, significance=TYPO_SIGNIFICANCE)
        ApprovedRevisionFactory(document=d2, significance=TYPO_SIGNIFICANCE)
        data = kb_overview_rows()
        self.assertEqual(True, data[0]["ready_for_l10n"])
        self.assertEqual(False, data[1]["ready_for_l10n"])

        ApprovedRevisionFactory(document=d1, significance=MEDIUM_SIGNIFICANCE)
        ApprovedRevisionFactory(
            document=d2, is_ready_for_localization=True, significance=MEDIUM_SIGNIFICANCE
        )
        data = kb_overview_rows()
        self.assertEqual(False, data[0]["ready_for_l10n"])
        self.assertEqual(True, data[1]["ready_for_l10n"])

    def test_revision_comment(self):
        d1 = DocumentFactory()
        rev1_d1 = RevisionFactory(document=d1)
        rev2_d1 = RevisionFactory(document=d1)
        d2 = DocumentFactory()
        ApprovedRevisionFactory(document=d2)
        rev1_d2 = RevisionFactory(document=d2)
        rev2_d2 = RevisionFactory(document=d2)

        WikiDocumentVisits.objects.create(document=d1, visits=20, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=d2, visits=10, period=LAST_30_DAYS)

        data = kb_overview_rows(user=UserFactory(is_staff=True, is_superuser=True))
        self.assertEqual(2, len(data))
        self.assertNotIn("latest_revision", data[0])
        self.assertNotIn("latest_revision", data[1])
        self.assertEqual(rev1_d1.comment, data[0]["revision_comment"])
        self.assertEqual(rev1_d2.comment, data[1]["revision_comment"])

        rev2_d1.is_approved = True
        rev2_d1.save()
        data = kb_overview_rows()
        self.assertNotIn("revision_comment", data[0])
        self.assertNotIn("latest_revision", data[1])
        self.assertTrue(data[0]["latest_revision"])
        self.assertEqual(rev1_d2.comment, data[1]["revision_comment"])

        rev2_d2.is_approved = True
        rev2_d2.save()
        data = kb_overview_rows()
        self.assertNotIn("revision_comment", data[0])
        self.assertNotIn("revision_comment", data[1])
        self.assertTrue(data[0]["latest_revision"])
        self.assertTrue(data[1]["latest_revision"])

    def test_needs_update(self):
        rev1 = ApprovedRevisionFactory()
        en_doc1 = rev1.document

        rev2 = ApprovedRevisionFactory(
            document__needs_change=True,
            document__needs_change_comment="Doc2 needs to be updated.",
        )
        en_doc2 = rev2.document

        trans_rev1 = TranslatedRevisionFactory(
            document__locale="de",
            document__parent__needs_change=True,
            document__parent__needs_change_comment="Doc3 needs to be updated.",
        )
        en_doc3 = trans_rev1.document.parent
        ApprovedRevisionFactory(document=en_doc3, significance=TYPO_SIGNIFICANCE)

        trans_rev2 = TranslatedRevisionFactory(
            document__locale="de",
            document__parent__needs_change=True,
            document__parent__needs_change_comment="Doc4 needs to be updated.",
        )
        en_doc4 = trans_rev2.document.parent
        ApprovedRevisionFactory(
            document=en_doc4, is_ready_for_localization=True, significance=MEDIUM_SIGNIFICANCE
        )

        WikiDocumentVisits.objects.create(document=en_doc1, visits=40, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=en_doc2, visits=30, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=en_doc3, visits=20, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=en_doc4, visits=10, period=LAST_30_DAYS)

        data = kb_overview_rows(locale="en-US")
        self.assertEqual(False, data[0]["needs_update"])
        self.assertEqual("", data[0]["needs_update_comment"])
        self.assertEqual(True, data[1]["needs_update"])
        self.assertEqual(en_doc2.needs_change_comment, data[1]["needs_update_comment"])
        self.assertEqual(True, data[2]["needs_update"])
        self.assertEqual(en_doc3.needs_change_comment, data[2]["needs_update_comment"])
        self.assertEqual(True, data[3]["needs_update"])
        self.assertEqual(en_doc4.needs_change_comment, data[3]["needs_update_comment"])

        data = kb_overview_rows(locale="de")
        self.assertNotIn("needs_update", data[0])
        self.assertNotIn("needs_update_comment", data[0])
        self.assertNotIn("needs_update", data[1])
        self.assertNotIn("needs_update_comment", data[1])
        self.assertEqual(False, data[2]["needs_update"])
        self.assertNotIn("needs_update_comment", data[2])
        self.assertEqual(True, data[3]["needs_update"])
        self.assertNotIn("needs_update_comment", data[3])

    def test_filter_by_category(self):
        ApprovedRevisionFactory(document__category=CATEGORIES[1][0])

        self.assertEqual(1, len(kb_overview_rows()))
        self.assertEqual(0, len(kb_overview_rows(category=CATEGORIES[0][0])))
        self.assertEqual(1, len(kb_overview_rows(category=CATEGORIES[1][0])))

    def test_num_visits(self):
        d1 = ApprovedRevisionFactory().document
        d2 = ApprovedRevisionFactory().document
        ApprovedRevisionFactory()
        ApprovedRevisionFactory()
        d3 = ApprovedRevisionFactory(
            document__restrict_to_groups=[GroupFactory(name="group1")]
        ).document

        WikiDocumentVisits.objects.create(document=d1, visits=5, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=d2, visits=1, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=d3, visits=4, period=LAST_30_DAYS)

        rows = kb_overview_rows(max=3)

        self.assertEqual(3, len(rows))
        self.assertEqual(rows[0]["num_visits"], 5)
        self.assertEqual(rows[0]["visits_ratio"], 1.0)
        self.assertEqual(rows[1]["num_visits"], 1)
        self.assertEqual(rows[1]["visits_ratio"], 0.2)
        self.assertEqual(rows[2]["num_visits"], None)
        self.assertNotIn("visits_ratio", rows[2])


class L10NOverviewTests(TestCase):
    """Tests for Overview readout"""

    def test_counting_unready_templates(self):
        """Templates without a ready-for-l10n rev don't count"""
        # Make a template with an approved but not-ready-for-l10n rev:
        d = TemplateDocumentFactory(is_localizable=True)
        r = ApprovedRevisionFactory(document=d, is_ready_for_localization=False)

        # It shouldn't show up in the total:
        self.assertEqual(0, l10n_overview_rows("de")["templates"]["denominator"])

        r.is_ready_for_localization = True
        r.save()
        self.assertEqual(1, l10n_overview_rows("de")["templates"]["denominator"])

    def test_counting_unready_docs(self):
        """Docs without a ready-for-l10n rev shouldn't count in total."""
        # Make a doc with an approved but not-ready-for-l10n rev:
        d = DocumentFactory(is_localizable=True)
        r = ApprovedRevisionFactory(document=d, is_ready_for_localization=False)

        # It shouldn't show up in the total:
        self.assertEqual(0, l10n_overview_rows("de")["all"]["denominator"])

        r.is_ready_for_localization = True
        r.save()
        self.assertEqual(1, l10n_overview_rows("de")["all"]["denominator"])

    def test_counting_unready_parents(self):
        """Translations with no ready revs don't count in numerator

        By dint of factoring, this also tests that templates whose
        parents....

        """
        parent_rev = RevisionFactory(
            document__is_localizable=True, is_approved=True, is_ready_for_localization=False
        )
        translation = DocumentFactory(
            parent=parent_rev.document, locale="de", is_localizable=False
        )
        RevisionFactory(document=translation, is_approved=True, based_on=parent_rev)
        self.assertEqual(0, l10n_overview_rows("de")["all"]["numerator"])

    def test_templates_and_docs_disjunct(self):
        """Make sure templates aren't included in the All Articles count."""
        t = TranslatedRevisionFactory(document__locale="de", is_approved=True)
        # It shows up in All when it's a normal doc:
        self.assertEqual(1, l10n_overview_rows("de")["all"]["numerator"])
        self.assertEqual(1, l10n_overview_rows("de")["all"]["denominator"])

        t.document.parent.title = t.document.title = "Template:thing"
        t.document.parent.category = TEMPLATES_CATEGORY
        # is_template will be automatically set for both templates, and so will
        # the child document's category.
        t.document.parent.save()
        t.document.save()
        # ...but not when it's a template:
        self.assertEqual(0, l10n_overview_rows("de")["all"]["numerator"])
        self.assertEqual(0, l10n_overview_rows("de")["all"]["denominator"])

    def test_not_counting_outdated(self):
        """Out-of-date translations shouldn't count as "done".

        "Out-of-date" can mean either moderately or majorly out of date. The
        only thing we don't care about is typo-level outdatedness.

        """
        t = TranslatedRevisionFactory(document__locale="de", is_approved=True)
        overview = l10n_overview_rows("de")
        self.assertEqual(1, overview["top-20"]["numerator"])
        self.assertEqual(1, overview["top-50"]["numerator"])
        self.assertEqual(1, overview["top-100"]["numerator"])
        self.assertEqual(1, overview["all"]["numerator"])

        # Update the parent with a typo-level revision:
        ApprovedRevisionFactory(
            document=t.document.parent,
            significance=TYPO_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        # Assert it still shows up in the numerators:
        overview = l10n_overview_rows("de")
        self.assertEqual(1, overview["top-20"]["numerator"])
        self.assertEqual(1, overview["top-50"]["numerator"])
        self.assertEqual(1, overview["top-100"]["numerator"])
        self.assertEqual(1, overview["all"]["numerator"])

        # Update the parent with a medium-level revision:
        ApprovedRevisionFactory(
            document=t.document.parent,
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True,
        )
        # Assert it no longer shows up in the numerators:
        overview = l10n_overview_rows("de")
        self.assertEqual(0, overview["all"]["numerator"])
        self.assertEqual(0, overview["top-20"]["numerator"])
        self.assertEqual(0, overview["top-50"]["numerator"])
        self.assertEqual(0, overview["top-100"]["numerator"])

    def test_not_counting_how_to_contribute(self):
        """Articles with the How to contribute category should not be counted."""
        t = TranslatedRevisionFactory(document__locale="de", is_approved=True)
        overview = l10n_overview_rows("de")
        self.assertEqual(1, overview["all"]["numerator"])
        self.assertEqual(1, overview["top-20"]["numerator"])
        self.assertEqual(1, overview["top-50"]["numerator"])
        self.assertEqual(1, overview["top-100"]["numerator"])

        # Update the parent with the How To Contribute category
        d = t.document.parent
        d.category = HOW_TO_CONTRIBUTE_CATEGORY
        d.save()

        overview = l10n_overview_rows("de")
        self.assertEqual(0, overview["all"]["numerator"])
        self.assertEqual(0, overview["top-20"]["numerator"])
        self.assertEqual(0, overview["top-50"]["numerator"])
        self.assertEqual(0, overview["top-100"]["numerator"])

    def test_not_counting_untranslated(self):
        """Translations with no approved revisions shouldn't count as done."""
        TranslatedRevisionFactory(document__locale="de", is_approved=False)
        overview = l10n_overview_rows("de")
        self.assertEqual(0, overview["top-20"]["numerator"])
        self.assertEqual(0, overview["top-50"]["numerator"])
        self.assertEqual(0, overview["top-100"]["numerator"])
        self.assertEqual(0, overview["all"]["numerator"])

    def test_not_counting_templates(self):
        """Articles in the Templates category should not be counted."""
        t = TranslatedRevisionFactory(document__locale="de", is_approved=True)
        overview = l10n_overview_rows("de")
        self.assertEqual(1, overview["all"]["numerator"])
        self.assertEqual(1, overview["top-20"]["numerator"])
        self.assertEqual(1, overview["top-50"]["numerator"])
        self.assertEqual(1, overview["top-100"]["numerator"])

        # Update the parent and translation to be a template
        d = t.document.parent
        d.title = "Template:Lorem Ipsum Dolor"
        d.category = TEMPLATES_CATEGORY
        d.save()
        t.document.title = "Template:Lorem Ipsum Dolor"
        t.document.save()

        overview = l10n_overview_rows("de")
        self.assertEqual(0, overview["all"]["numerator"])
        self.assertEqual(0, overview["top-20"]["numerator"])
        self.assertEqual(0, overview["top-50"]["numerator"])
        self.assertEqual(0, overview["top-100"]["numerator"])

    def test_by_product(self):
        """Test the product filtering of the overview."""
        p = ProductFactory(title="Firefox", slug="firefox")
        t = TranslatedRevisionFactory(is_approved=True, document__locale="de")

        self.assertEqual(0, l10n_overview_rows("de", product=p)["all"]["numerator"])
        self.assertEqual(0, l10n_overview_rows("de", product=p)["all"]["denominator"])

        t.document.parent.products.add(p)

        self.assertEqual(1, l10n_overview_rows("de", product=p)["all"]["numerator"])
        self.assertEqual(1, l10n_overview_rows("de", product=p)["all"]["denominator"])

    def test_redirects_are_ignored(self):
        """Verify that redirects aren't counted in the overview."""
        TranslatedRevisionFactory(document__locale="de", is_approved=True)

        self.assertEqual(1, l10n_overview_rows("de")["all"]["numerator"])

        # A redirect shouldn't affect any of the tests.
        RedirectRevisionFactory(
            document__is_localizable=True,
            document__is_template=True,
            is_ready_for_localization=True,
        )

        overview = l10n_overview_rows("de")
        self.assertEqual(1, overview["all"]["numerator"])
        self.assertEqual(1, overview["top-20"]["numerator"])
        self.assertEqual(1, overview["top-50"]["numerator"])
        self.assertEqual(1, overview["top-100"]["numerator"])

    def test_miscounting_archived(self):
        """
        Verify that the l10n overview readout treats archived docs consistently.

        Bug 1012384
        """
        locale = "nl"
        parent1 = DocumentFactory(category=CANNED_RESPONSES_CATEGORY, is_archived=False)
        translation1 = DocumentFactory(parent=parent1, locale=locale)
        parent2 = DocumentFactory(category=CANNED_RESPONSES_CATEGORY, is_archived=True)
        translation2 = DocumentFactory(parent=parent2, locale=locale)

        trans_rev1 = ApprovedRevisionFactory(document=parent1, is_ready_for_localization=True)
        ApprovedRevisionFactory(document=translation1, based_on=trans_rev1)
        trans_rev2 = ApprovedRevisionFactory(document=parent2, is_ready_for_localization=True)
        ApprovedRevisionFactory(document=translation2, based_on=trans_rev2)

        # Document.save() will enforce that parents and translations share is_archived.
        # The point of this is to test what happens when that isn't true though,
        # so bypass Document.save().
        translation2.is_archived = False
        ModelBase.save(translation2)
        self.assertEqual(translation2.is_archived, False)

        overview = l10n_overview_rows(locale)
        self.assertEqual(1, overview["all"]["denominator"])
        self.assertEqual(1, overview["all"]["numerator"])


class UnreviewedChangesTests(ReadoutTestCase):
    """Tests for the Unreviewed Changes readout

    I'm not trying to cover every slice of the Venn diagram--just the tricky
    bits.

    """

    readout = UnreviewedReadout

    def test_unrevieweds_after_current(self):
        """Show unreviewed revisions with later creation dates than current"""
        rev1 = TranslatedRevisionFactory(
            document__locale="de", reviewed=None, is_approved=True, created=datetime(2000, 1, 1)
        )
        rev2 = RevisionFactory(reviewed=None, document=rev1.document, created=datetime(2000, 2, 1))
        rev3 = RevisionFactory(reviewed=None, document=rev1.document, created=datetime(2000, 3, 1))

        doc_de = TranslatedRevisionFactory(
            document__locale="de", reviewed=None, is_approved=True, created=datetime(2023, 1, 1)
        ).document
        rev4 = TranslatedRevisionFactory(
            document=doc_de, reviewed=None, is_approved=False, created=datetime(2023, 1, 2)
        )
        rev5 = RevisionFactory(reviewed=None, document=rev4.document, created=datetime(2023, 2, 1))
        rev6 = RevisionFactory(reviewed=None, document=rev4.document, created=datetime(2023, 3, 1))

        group1 = GroupFactory(name="group1")
        doc_en = DocumentFactory(restrict_to_groups=[group1])
        doc_de = DocumentFactory(parent=doc_en, locale="de")
        TranslatedRevisionFactory(
            document=doc_de, reviewed=None, is_approved=False, created=datetime(2023, 4, 1)
        )
        RevisionFactory(reviewed=None, document=doc_de, created=datetime(2023, 5, 1))
        RevisionFactory(reviewed=None, document=doc_de, created=datetime(2023, 6, 1))
        rev7 = RevisionFactory(reviewed=None, document=doc_en, created=datetime(2023, 7, 15))
        rev8 = RevisionFactory(reviewed=None, document=doc_en, created=datetime(2023, 8, 20))

        WikiDocumentVisits.objects.create(document=rev1.document, visits=5, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=rev4.document, visits=3, period=LAST_30_DAYS)
        WikiDocumentVisits.objects.create(document=doc_de, visits=2, period=LAST_30_DAYS)

        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["title"], rev1.document.title)
        self.assertEqual(rows[0]["visits"], 5)
        self.assertEqual(rows[0]["updated"], datetime(2000, 3, 1))
        self.assertEqual(
            rows[0]["users"],
            ", ".join(
                sorted(
                    [
                        rev2.creator.username,
                        rev3.creator.username,
                    ]
                )
            ),
        )
        self.assertEqual(rows[1]["title"], rev4.document.title)
        self.assertEqual(rows[1]["visits"], 3)
        self.assertEqual(rows[1]["updated"], datetime(2023, 3, 1))
        self.assertEqual(
            rows[1]["users"],
            ", ".join(
                sorted(
                    [
                        rev4.creator.username,
                        rev5.creator.username,
                        rev6.creator.username,
                    ]
                )
            ),
        )

        # The English document is restricted.
        rows = self.rows(locale="en-US")
        self.assertEqual(len(rows), 0)

        # But members of group1 can see it.
        rows = self.rows(user=UserFactory(groups=[group1]), locale="en-US")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], doc_en.title)
        self.assertEqual(rows[0]["visits"], None)
        self.assertEqual(rows[0]["updated"], datetime(2023, 8, 20))
        self.assertEqual(
            rows[0]["users"],
            ", ".join(
                sorted(
                    [
                        rev7.creator.username,
                        rev8.creator.username,
                    ]
                )
            ),
        )

    def test_current_revision_null(self):
        """Show all unreviewed revisions if none have been approved yet."""
        doc_de = TranslatedRevisionFactory(
            is_approved=True, reviewed=None, document__locale="de"
        ).document
        unreviewed = TranslatedRevisionFactory(is_approved=False, reviewed=None, document=doc_de)
        assert unreviewed.document.title in self.titles()

    def test_rejected_newer_than_current(self):
        """Don't show reviewed but unapproved revs newer than current rev"""
        rejected = TranslatedRevisionFactory(
            document__locale="de", reviewed=datetime.now(), is_approved=False
        )
        assert rejected.document.title not in self.titles()

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = ProductFactory(title="Firefox", slug="firefox")
        doc_de = TranslatedRevisionFactory(
            is_approved=True, reviewed=None, document__locale="de"
        ).document
        unreviewed = TranslatedRevisionFactory(is_approved=False, reviewed=None, document=doc_de)

        # There shouldn't be any rows yet.
        self.assertEqual(0, len(self.rows(product=p)))

        # Add the product to the parent document, and verify it shows up.
        unreviewed.document.parent.products.add(p)
        self.assertEqual(self.row(product=p)["title"], unreviewed.document.title)


class MostVisitedDefaultLanguageTests(ReadoutTestCase):
    """Tests for the Most Visited Default Language readout."""

    readout = MostVisitedDefaultLanguageReadout

    def test_by_product(self):
        """Test the product filtering of the readout."""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        p = ProductFactory(title="Firefox", slug="firefox")
        d = DocumentFactory()
        ApprovedRevisionFactory(document=d)

        # There shouldn't be any rows yet.
        self.assertEqual(0, len(self.rows(locale=locale, product=p)))

        # Add the product to the document, and verify it shows up.
        d.products.add(p)
        self.assertEqual(self.row(locale=locale, product=p)["title"], d.title)

    def test_redirects_not_shown(self):
        """Redirects shouldn't appear in Most Visited readout."""
        RedirectRevisionFactory(is_ready_for_localization=True)
        self.assertEqual(0, len(self.titles()))


class TemplateTests(ReadoutTestCase):
    readout = TemplateReadout

    def test_only_templates(self):
        """Test that only templates are shown"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        p = ProductFactory(title="Firefox", slug="firefox")

        d = DocumentFactory(products=[p])
        t = TemplateDocumentFactory(products=[p])
        ApprovedRevisionFactory(document=t)
        ApprovedRevisionFactory(document=d)
        ApprovedRevisionFactory(document=TemplateDocumentFactory())
        rt = TemplateDocumentFactory(
            restrict_to_groups=[GroupFactory(name="group1")], products=[p]
        )
        ApprovedRevisionFactory(document=rt)

        self.assertEqual(1, len(self.rows(locale=locale, product=p)))
        self.assertEqual(t.title, self.row(locale=locale, product=p)["title"])
        self.assertEqual("Updated", self.row(locale=locale, product=p)["status"])

    def test_needs_changes(self):
        """Test status for article that needs changes"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        d = TemplateDocumentFactory(needs_change=True)
        ApprovedRevisionFactory(document=d)

        row = self.row(locale=locale)

        self.assertEqual(row["title"], d.title)
        self.assertEqual(str(row["status"]), "Changes Needed")

    def test_needs_review(self):
        """Test status for article that needs review"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        d = TemplateDocumentFactory()
        ApprovedRevisionFactory(document=d)
        RevisionFactory(document=d)

        row = self.row(locale=locale)

        self.assertEqual(row["title"], d.title)
        self.assertEqual(str(row["status"]), "Review Needed")

    def test_unready_for_l10n(self):
        """Test status for article that is not ready for l10n"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        d = TemplateDocumentFactory()
        RevisionFactory(document=d, is_ready_for_localization=True)
        ApprovedRevisionFactory(
            document=d, is_ready_for_localization=False, significance=MAJOR_SIGNIFICANCE
        )

        row = self.row(locale=locale)

        self.assertEqual(row["title"], d.title)
        self.assertEqual(str(row["status"]), "Changes Not Ready For Localization")


class HowToContributeTests(ReadoutTestCase):
    readout = HowToContributeReadout

    def test_only_how_to_contribute(self):
        """Test that only How To Contribute articles are shown"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        p = ProductFactory(title="Firefox", slug="firefox")

        d1 = DocumentFactory(products=[p])
        d2 = DocumentFactory(title="How To", category=HOW_TO_CONTRIBUTE_CATEGORY, products=[p])

        ApprovedRevisionFactory(document=d1)
        ApprovedRevisionFactory(document=d2)

        self.assertEqual(1, len(self.rows(locale=locale, product=p)))
        self.assertEqual(d2.title, self.row(locale=locale, product=p)["title"])
        self.assertEqual("Updated", self.row(locale=locale, product=p)["status"])


class AdministrationTests(ReadoutTestCase):
    readout = AdministrationReadout

    def test_only_how_to_contribute(self):
        """Test that only Administration articles are shown"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        p = ProductFactory(title="Firefox", slug="firefox")

        d1 = DocumentFactory(products=[p])
        d2 = DocumentFactory(title="Admin", category=ADMINISTRATION_CATEGORY, products=[p])

        ApprovedRevisionFactory(document=d1)
        ApprovedRevisionFactory(document=d2)

        self.assertEqual(1, len(self.rows(locale=locale, product=p)))
        self.assertEqual(d2.title, self.row(locale=locale, product=p)["title"])
        self.assertEqual("Updated", self.row(locale=locale, product=p)["status"])


class MostVisitedTranslationsTests(ReadoutTestCase):
    """Tests for the Most Visited Translations readout

    This is an especially tricky readout, since it effectively implements a
    superset of all other readouts' status discriminators.

    """

    readout = MostVisitedTranslationsReadout

    def test_unreviewed(self):
        """Assert articles in need of review are labeled as such."""
        unreviewed = TranslatedRevisionFactory(
            document__locale="de", reviewed=None, is_approved=False
        )

        # A document will be excluded for anonymous users, if its
        # only translation doesn't have an approved revision.
        self.assertEqual(len(self.rows()), 0)

        # However, reviewers can.
        reviewer = UserFactory()
        add_permission(reviewer, Revision, "review_revision")
        row = self.row(user=reviewer)
        self.assertEqual(row["title"], unreviewed.document.title)
        self.assertEqual(row["status"], "Review Needed")

    def test_unlocalizable(self):
        """Unlocalizable docs shouldn't show up in the list."""
        ApprovedRevisionFactory(document__is_localizable=False)
        self.assertRaises(IndexError, self.row)

    def _test_significance(self, significance, status):
        """
        Assert that a translation out of date due to a
        `significance`-level update to the original article shows
        status `status`.

        """
        translation = TranslatedRevisionFactory(document__locale="de", is_approved=True)
        ApprovedRevisionFactory(
            document=translation.document.parent,
            is_ready_for_localization=True,
            significance=significance,
        )
        row = self.row()
        self.assertEqual(row["title"], translation.document.title)
        self.assertEqual(row["status"], status)

    def test_out_of_date(self):
        """Assert out-of-date translations are labeled as such."""
        self._test_significance(MAJOR_SIGNIFICANCE, "Immediate Update Needed")

    def test_update_needed(self):
        """Assert update-needed translations are labeled as such."""
        self._test_significance(MEDIUM_SIGNIFICANCE, "Update Needed")

    def test_untranslated(self):
        """Assert untranslated documents are labeled as such."""
        untranslated = ApprovedRevisionFactory(is_ready_for_localization=True)
        row = self.row()
        self.assertEqual(row["title"], untranslated.document.title)
        self.assertEqual(str(row["status"]), "Translation Needed")

    def test_up_to_date(self):
        """Show up-to-date translations have no status, just a happy class."""
        translation = TranslatedRevisionFactory(document__locale="de", is_approved=True)
        row = self.row()
        self.assertEqual(row["title"], translation.document.title)
        self.assertEqual(str(row["status"]), "Updated")
        self.assertEqual(row["status_class"], "ok")

    def test_one_rejected_revision(self):
        """Translation with 1 rejected rev shows as Needs Translation"""
        TranslatedRevisionFactory(
            document__locale="de", is_approved=False, reviewed=datetime.now()
        )

        # A document will be excluded for anonymous users, if its
        # only translation doesn't have an approved revision.
        self.assertEqual(len(self.rows()), 0)

        # However, reviewers can.
        reviewer = UserFactory()
        add_permission(reviewer, Revision, "review_revision")
        self.assertEqual("untranslated", self.row(user=reviewer)["status_class"])

    def test_spam(self):
        """Don't offer unapproved (often spam) articles for translation."""
        ApprovedRevisionFactory()
        self.assertEqual([], MostVisitedTranslationsReadout(MockRequest()).rows())

    def test_consider_max_significance(self):
        """Use max significance for determining change significance

        When determining how significantly an article has changed
        since translation, use the max significance of the approved
        revisions, not just that of the latest ready-to-localize one.
        """
        translation = TranslatedRevisionFactory(document__locale="de", is_approved=True)
        ApprovedRevisionFactory(
            document=translation.document.parent,
            is_ready_for_localization=False,  # should still count
            significance=MAJOR_SIGNIFICANCE,
        )
        ApprovedRevisionFactory(
            document=translation.document.parent,
            is_ready_for_localization=True,
            significance=MEDIUM_SIGNIFICANCE,
        )
        row = self.row()
        self.assertEqual(row["title"], translation.document.title)
        self.assertEqual(str(row["status"]), "Immediate Update Needed")

    def test_consider_only_approved_significances(self):
        """Consider only approved significances when computing the max."""
        translation = TranslatedRevisionFactory(document__locale="de", is_approved=True)
        RevisionFactory(
            document=translation.document.parent,
            is_approved=False,  # shouldn't count
            is_ready_for_localization=False,
            significance=MAJOR_SIGNIFICANCE,
        )
        RevisionFactory(
            document=translation.document.parent,
            is_approved=True,
            is_ready_for_localization=True,
            significance=MEDIUM_SIGNIFICANCE,
        )
        row = self.row()
        self.assertEqual(row["title"], translation.document.title)
        # This should show as medium significance, because the revision with
        # major significance is unapproved:
        self.assertEqual(str(row["status"]), "Update Needed")

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = ProductFactory(title="Firefox", slug="firefox")
        r = TranslatedRevisionFactory(document__locale="de", is_approved=True)
        d = r.document

        # There shouldn't be any rows yet.
        self.assertEqual(0, len(self.rows(product=p)))

        # Add the product to the parent document, and verify it shows up.
        d.parent.products.add(p)
        self.assertEqual(self.row(product=p)["title"], d.title)


class TemplateTranslationsTests(ReadoutTestCase):
    """Tests for the Template Translations readout"""

    readout = TemplateTranslationsReadout

    def test_not_template(self):
        """Documents that are not templates shouldn't show up in the list."""
        TranslatedRevisionFactory(document__locale="de", is_approved=False)
        self.assertRaises(IndexError, self.row)

    def test_untranslated(self):
        """Assert untranslated templates are labeled as such."""
        d = TemplateDocumentFactory()
        untranslated = ApprovedRevisionFactory(document=d, is_ready_for_localization=True)
        row = self.row()
        self.assertEqual(row["title"], untranslated.document.title)
        self.assertEqual(str(row["status"]), "Translation Needed")

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = ProductFactory(title="Firefox", slug="firefox")
        d = TemplateDocumentFactory()
        ApprovedRevisionFactory(document=d, is_ready_for_localization=True)

        # There shouldn't be any rows yet.
        self.assertEqual(0, len(self.rows(product=p)))

        # Add the product to the document, and verify it shows up.
        d.products.add(p)
        self.assertEqual(self.row(product=p)["title"], d.title)


class UnreadyTests(ReadoutTestCase):
    """Tests for UnreadyForLocalizationReadout"""

    readout = UnreadyForLocalizationReadout

    def test_no_approved_revs(self):
        """Articles with no approved revisions should not appear."""
        RevisionFactory(
            is_approved=False, is_ready_for_localization=False, significance=MAJOR_SIGNIFICANCE
        )
        self.assertEqual([], self.titles())

    def test_unapproved_revs(self):
        """Don't show articles with unreviewed or rejected revs after latest"""
        d = DocumentFactory()
        RevisionFactory(document=d, is_approved=True, is_ready_for_localization=True)
        RevisionFactory(
            document=d, is_approved=False, reviewed=None, is_ready_for_localization=False
        )
        RevisionFactory(
            document=d, is_approved=False, reviewed=datetime.now(), is_ready_for_localization=False
        )
        self.assertEqual([], self.titles())

    def test_first_rev(self):
        """If an article's first revision is approved, show the article.

        This also conveniently tests that documents with no
        latest_localizable_revision are not necessarily excluded.

        """
        r = ApprovedRevisionFactory(
            reviewed=datetime.now(), is_ready_for_localization=False, significance=None
        )
        self.assertEqual([r.document.title], self.titles())

    def test_insignificant_revs(self):
        # Articles with approved, unready, but insignificant revisions
        # newer than their latest ready-for-l10n ones should not
        # appear.
        ready = ApprovedRevisionFactory(is_ready_for_localization=True)
        ApprovedRevisionFactory(
            document=ready.document,
            is_ready_for_localization=False,
            significance=TYPO_SIGNIFICANCE,
        )
        self.assertEqual([], self.titles())

    def test_significant_revs(self):
        # Articles with approved, significant, but unready revisions
        # newer than their latest ready-for-l10n ones should appear.
        ready = ApprovedRevisionFactory(is_ready_for_localization=True)
        ApprovedRevisionFactory(
            document=ready.document,
            is_ready_for_localization=False,
            significance=MEDIUM_SIGNIFICANCE,
        )
        self.assertEqual([ready.document.title], self.titles())

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = ProductFactory(title="Firefox", slug="firefox")
        ready = ApprovedRevisionFactory(is_ready_for_localization=True)
        ApprovedRevisionFactory(
            document=ready.document,
            is_ready_for_localization=False,
            significance=MEDIUM_SIGNIFICANCE,
        )

        # There shouldn't be any rows yet.
        self.assertEqual(0, len(self.rows(product=p)))

        # Add the product to the document, and verify it shows up.
        ready.document.products.add(p)
        self.assertEqual(self.row(product=p)["title"], ready.document.title)


class NeedsChangesTests(ReadoutTestCase):
    """Tests for the Needs Changes readout."""

    readout = NeedsChangesReadout

    def test_needs_change(self):
        """A document marked with needs_change=True should show up."""
        document = DocumentFactory(
            needs_change=True, needs_change_comment="Please update for Firefox.next"
        )
        ApprovedRevisionFactory(document=document)
        titles = self.titles()
        self.assertEqual(1, len(titles))
        assert document.title in titles

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = ProductFactory(title="Firefox", slug="firefox")
        d = DocumentFactory(
            needs_change=True, needs_change_comment="Please update for Firefox.next"
        )
        ApprovedRevisionFactory(document=d)

        # There shouldn't be any rows yet.
        self.assertEqual(0, len(self.rows(product=p)))

        # Add the product to the document, and verify it shows up.
        d.products.add(p)
        self.assertEqual(self.row(product=p)["title"], d.title)


class CannedResponsesTests(ReadoutTestCase):
    readout = CannedResponsesReadout

    def test_canned(self):
        """Test the readout."""
        ApprovedRevisionFactory(
            is_ready_for_localization=True, document__category=CANNED_RESPONSES_CATEGORY
        )
        self.assertEqual(1, len(self.rows()))

    def test_translation_state(self):
        eng_doc = DocumentFactory(category=CANNED_RESPONSES_CATEGORY)
        eng_rev = ApprovedRevisionFactory(is_ready_for_localization=True, document=eng_doc)

        self.assertEqual("untranslated", self.row()["status_class"])

        # Now translate it, but don't approve
        de_doc = DocumentFactory(category=CANNED_RESPONSES_CATEGORY, parent=eng_doc, locale="de")
        de_rev = RevisionFactory(
            document=de_doc, based_on=eng_rev, is_approved=False, reviewed=None
        )

        # A document will be excluded for anonymous users, if its
        # only translation doesn't have an approved revision.
        self.assertEqual(len(self.rows()), 0)

        # However, reviewers can.
        reviewer = UserFactory()
        add_permission(reviewer, Revision, "review_revision")
        self.assertEqual("review", self.row(user=reviewer)["status_class"])

        # Approve it, so now every this is ok.
        de_rev.is_approved = True
        de_rev.save()

        self.assertEqual("ok", self.row()["status_class"])

        # Now update the parent, so it becomes minorly out of date
        ApprovedRevisionFactory(
            is_ready_for_localization=True, document=eng_doc, significance=MEDIUM_SIGNIFICANCE
        )

        self.assertEqual("update", self.row()["status_class"])

        # Now update the parent, so it becomes majorly out of date
        ApprovedRevisionFactory(
            is_ready_for_localization=True, document=eng_doc, significance=MAJOR_SIGNIFICANCE
        )

        self.assertEqual("out-of-date", self.row()["status_class"])

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = ProductFactory(title="Firefox", slug="firefox")
        d = DocumentFactory(title="Foo", category=CANNED_RESPONSES_CATEGORY)
        ApprovedRevisionFactory(document=d, is_ready_for_localization=True)

        # There shouldn't be any rows yet.
        self.assertEqual(0, len(self.rows(product=p)))

        # Add the product to the document, and verify it shows up.
        d.products.add(p)
        self.assertEqual(1, len(self.rows(product=p)))
        self.assertEqual(self.row(product=p)["title"], d.title)
