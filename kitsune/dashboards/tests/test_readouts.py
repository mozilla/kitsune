from datetime import datetime

from django.conf import settings

from nose.tools import eq_

from kitsune.dashboards.readouts import (
    UnreviewedReadout, kb_overview_rows,
    TemplateTranslationsReadout, l10n_overview_rows,
    MostVisitedDefaultLanguageReadout,
    MostVisitedTranslationsReadout,
    UnreadyForLocalizationReadout,
    NeedsChangesReadout,
    TemplateReadout,
    HowToContributeReadout,
    AdministrationReadout, CannedResponsesReadout)
from kitsune.products.tests import product
from kitsune.sumo.tests import TestCase
from kitsune.wiki.config import (
    MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE, TYPO_SIGNIFICANCE, HOW_TO_CONTRIBUTE_CATEGORY,
    ADMINISTRATION_CATEGORY, CANNED_RESPONSES_CATEGORY, TEMPLATES_CATEGORY)
from kitsune.wiki.config import CATEGORIES
from kitsune.wiki.tests import (
    revision, translated_revision, document,
    DocumentFactory, RevisionFactory, TemplateDocumentFactory, ApprovedRevisionFactory)


class MockRequest(object):
    LANGUAGE_CODE = 'de'  # Same locale as translated_revision uses by default


class ReadoutTestCase(TestCase):
    """Test case for one readout. Provides some convenience methods."""

    def rows(self, locale=None, product=None):
        """Return the rows show by the readout this class tests."""
        return self.readout(
            MockRequest(), locale=locale, product=product).rows()

    def row(self, locale=None, product=None):
        """Return first row shown by the readout this class tests."""
        return self.rows(locale=locale, product=product)[0]

    def titles(self, locale=None, product=None):
        """Return the titles shown by the Unreviewed Changes readout."""
        return [row['title'] for row in self.readout(
                MockRequest(), locale=locale, product=product).rows()]


class KBOverviewTests(TestCase):
    def test_unapproved_articles(self):
        eq_(0, len(kb_overview_rows()))

        d = document(save=True)
        revision(document=d, save=True)

        eq_(1, len(kb_overview_rows()))

    def test_ready_for_l10n(self):
        d = document(save=True)
        r = revision(document=d, save=True)
        d.current_revision = r
        d.save()

        data = kb_overview_rows()
        eq_(1, len(data))
        eq_(False, data[0]['ready_for_l10n'])

        revision(document=d, is_approved=True, is_ready_for_localization=True, save=True)

        data = kb_overview_rows()
        eq_(True, data[0]['ready_for_l10n'])

    def test_filter_by_category(self):
        d = document(save=True, category=CATEGORIES[1][0])
        revision(document=d, save=True)

        eq_(1, len(kb_overview_rows()))
        eq_(0, len(kb_overview_rows(category=CATEGORIES[0][0])))
        eq_(1, len(kb_overview_rows(category=CATEGORIES[1][0])))


class L10NOverviewTests(TestCase):
    """Tests for Overview readout"""

    def test_counting_unready_templates(self):
        """Templates without a ready-for-l10n rev don't count"""
        # Make a template with an approved but not-ready-for-l10n rev:
        d = TemplateDocumentFactory(is_localizable=True)
        r = ApprovedRevisionFactory(document=d, is_ready_for_localization=False)

        # It shouldn't show up in the total:
        eq_(0, l10n_overview_rows('de')['templates']['denominator'])

        r.is_ready_for_localization = True
        r.save()
        eq_(1, l10n_overview_rows('de')['templates']['denominator'])

    def test_counting_unready_docs(self):
        """Docs without a ready-for-l10n rev shouldn't count in total."""
        # Make a doc with an approved but not-ready-for-l10n rev:
        d = DocumentFactory(is_localizable=True)
        r = ApprovedRevisionFactory(document=d, is_ready_for_localization=False)

        # It shouldn't show up in the total:
        eq_(0, l10n_overview_rows('de')['all']['denominator'])

        r.is_ready_for_localization = True
        r.save()
        eq_(1, l10n_overview_rows('de')['all']['denominator'])

    def test_counting_unready_parents(self):
        """Translations with no ready revs don't count in numerator

        By dint of factoring, this also tests that templates whose
        parents....

        """
        parent_rev = revision(document=document(is_localizable=True,
                                                save=True),
                              is_approved=True,
                              is_ready_for_localization=False,
                              save=True)
        translation = document(parent=parent_rev.document,
                               locale='de',
                               is_localizable=False,
                               save=True)
        revision(document=translation,
                 is_approved=True,
                 based_on=parent_rev,
                 save=True)
        eq_(0, l10n_overview_rows('de')['all']['numerator'])

    def test_templates_and_docs_disjunct(self):
        """Make sure templates aren't included in the All Articles count."""
        t = translated_revision(is_approved=True, save=True)
        # It shows up in All when it's a normal doc:
        eq_(1, l10n_overview_rows('de')['all']['numerator'])
        eq_(1, l10n_overview_rows('de')['all']['denominator'])

        t.document.parent.title = t.document.title = 'Template:thing'
        t.document.parent.category = TEMPLATES_CATEGORY
        # is_template will be automatically set for both templates, and so will
        # the child document's category.
        t.document.parent.save()
        t.document.save()
        # ...but not when it's a template:
        eq_(0, l10n_overview_rows('de')['all']['numerator'])
        eq_(0, l10n_overview_rows('de')['all']['denominator'])

    def test_not_counting_outdated(self):
        """Out-of-date translations shouldn't count as "done".

        "Out-of-date" can mean either moderately or majorly out of date. The
        only thing we don't care about is typo-level outdatedness.

        """
        t = translated_revision(is_approved=True, save=True)
        overview = l10n_overview_rows('de')
        eq_(1, overview['top-20']['numerator'])
        eq_(1, overview['top-50']['numerator'])
        eq_(1, overview['top-100']['numerator'])
        eq_(1, overview['all']['numerator'])

        # Update the parent with a typo-level revision:
        revision(document=t.document.parent,
                 significance=TYPO_SIGNIFICANCE,
                 is_approved=True,
                 is_ready_for_localization=True,
                 save=True)
        # Assert it still shows up in the numerators:
        overview = l10n_overview_rows('de')
        eq_(1, overview['top-20']['numerator'])
        eq_(1, overview['top-50']['numerator'])
        eq_(1, overview['top-100']['numerator'])
        eq_(1, overview['all']['numerator'])

        # Update the parent with a medium-level revision:
        revision(document=t.document.parent,
                 significance=MEDIUM_SIGNIFICANCE,
                 is_approved=True,
                 is_ready_for_localization=True,
                 save=True)
        # Assert it no longer shows up in the numerators:
        overview = l10n_overview_rows('de')
        eq_(0, overview['all']['numerator'])
        eq_(0, overview['top-20']['numerator'])
        eq_(0, overview['top-50']['numerator'])
        eq_(0, overview['top-100']['numerator'])

    def test_not_counting_how_to_contribute(self):
        """Articles with the How to contribute category should not be counted.
        """
        t = translated_revision(is_approved=True, save=True)
        overview = l10n_overview_rows('de')
        eq_(1, overview['all']['numerator'])
        eq_(1, overview['top-20']['numerator'])
        eq_(1, overview['top-50']['numerator'])
        eq_(1, overview['top-100']['numerator'])

        # Update the parent with the How To Contribute category
        d = t.document.parent
        d.category = HOW_TO_CONTRIBUTE_CATEGORY
        d.save()

        overview = l10n_overview_rows('de')
        eq_(0, overview['all']['numerator'])
        eq_(0, overview['top-20']['numerator'])
        eq_(0, overview['top-50']['numerator'])
        eq_(0, overview['top-100']['numerator'])

    def test_not_counting_untranslated(self):
        """Translations with no approved revisions shouldn't count as done.
        """
        translated_revision(is_approved=False, save=True)
        overview = l10n_overview_rows('de')
        eq_(0, overview['top-20']['numerator'])
        eq_(0, overview['top-50']['numerator'])
        eq_(0, overview['top-100']['numerator'])
        eq_(0, overview['all']['numerator'])

    def test_not_counting_templates(self):
        """Articles in the Templates category should not be counted.
        """
        t = translated_revision(is_approved=True, save=True)
        overview = l10n_overview_rows('de')
        eq_(1, overview['all']['numerator'])
        eq_(1, overview['top-20']['numerator'])
        eq_(1, overview['top-50']['numerator'])
        eq_(1, overview['top-100']['numerator'])

        # Update the parent and translation to be a template
        d = t.document.parent
        d.title = 'Template:Lorem Ipsum Dolor'
        d.category = TEMPLATES_CATEGORY
        d.save()
        t.document.title = 'Template:Lorem Ipsum Dolor'
        t.document.save()

        overview = l10n_overview_rows('de')
        eq_(0, overview['all']['numerator'])
        eq_(0, overview['top-20']['numerator'])
        eq_(0, overview['top-50']['numerator'])
        eq_(0, overview['top-100']['numerator'])

    def test_by_product(self):
        """Test the product filtering of the overview."""
        p = product(title='Firefox', slug='firefox', save=True)
        t = translated_revision(is_approved=True, save=True)

        eq_(0, l10n_overview_rows('de', product=p)['all']['numerator'])
        eq_(0, l10n_overview_rows('de', product=p)['all']['denominator'])

        t.document.parent.products.add(p)

        eq_(1, l10n_overview_rows('de', product=p)['all']['numerator'])
        eq_(1, l10n_overview_rows('de', product=p)['all']['denominator'])

    def test_redirects_are_ignored(self):
        """Verify that redirects aren't counted in the overview."""
        translated_revision(is_approved=True, save=True)

        eq_(1, l10n_overview_rows('de')['all']['numerator'])

        # A redirect shouldn't affect any of the tests.
        revision(document=document(title='A redirect',
                                   is_localizable=True,
                                   is_template=True,
                                   save=True),
                 is_ready_for_localization=True,
                 is_approved=True,
                 content='REDIRECT [[An article]]',
                 save=True)

        overview = l10n_overview_rows('de')
        eq_(1, overview['all']['numerator'])
        eq_(1, overview['top-20']['numerator'])
        eq_(1, overview['top-50']['numerator'])
        eq_(1, overview['top-100']['numerator'])


class UnreviewedChangesTests(ReadoutTestCase):
    """Tests for the Unreviewed Changes readout

    I'm not trying to cover every slice of the Venn diagram--just the tricky
    bits.

    """
    readout = UnreviewedReadout

    def test_unrevieweds_after_current(self):
        """Show unreviewed revisions with later creation dates than current
        """
        current = translated_revision(is_approved=True, save=True,
                                      created=datetime(2000, 1, 1))
        unreviewed = revision(document=current.document, save=True,
                              created=datetime(2000, 2, 1))
        assert unreviewed.document.title in self.titles()

    def test_current_revision_null(self):
        """Show all unreviewed revisions if none have been approved yet."""
        unreviewed = translated_revision(save=True)
        assert unreviewed.document.title in self.titles()

    def test_rejected_newer_than_current(self):
        """Don't show reviewed but unapproved revs newer than current rev"""
        rejected = translated_revision(reviewed=datetime.now(), save=True)
        assert rejected.document.title not in self.titles()

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = product(title='Firefox', slug='firefox', save=True)
        unreviewed = translated_revision(save=True)

        # There shouldn't be any rows yet.
        eq_(0, len(self.rows(product=p)))

        # Add the product to the parent document, and verify it shows up.
        unreviewed.document.parent.products.add(p)
        eq_(self.row(product=p)['title'], unreviewed.document.title)


class MostVisitedDefaultLanguageTests(ReadoutTestCase):
    """Tests for the Most Visited Default Language readout."""
    readout = MostVisitedDefaultLanguageReadout

    def test_by_product(self):
        """Test the product filtering of the readout."""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        p = product(title='Firefox', slug='firefox', save=True)
        d = document(save=True)
        revision(document=d, is_approved=True, save=True)

        # There shouldn't be any rows yet.
        eq_(0, len(self.rows(locale=locale, product=p)))

        # Add the product to the document, and verify it shows up.
        d.products.add(p)
        eq_(self.row(locale=locale, product=p)['title'], d.title)

    def test_redirects_not_shown(self):
        """Redirects shouldn't appear in Most Visited readout."""
        revision(is_approved=True, is_ready_for_localization=True,
                 content='REDIRECT [[Foo Bar]]', save=True)

        eq_(0, len(self.titles()))


class TemplateTests(ReadoutTestCase):
    readout = TemplateReadout

    def test_only_templates(self):
        """Test that only templates are shown"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        p = product(title='Firefox', slug='firefox', save=True)

        d = DocumentFactory(products=[p])
        t = TemplateDocumentFactory(products=[p])
        ApprovedRevisionFactory(document=d)
        ApprovedRevisionFactory(document=TemplateDocumentFactory())

        eq_(1, len(self.rows(locale=locale, product=p)))
        eq_(t.title, self.row(locale=locale, product=p)['title'])
        eq_(u'', self.row(locale=locale, product=p)['status'])

    def test_needs_changes(self):
        """Test status for article that needs changes"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        d = TemplateDocumentFactory(needs_change=True)
        ApprovedRevisionFactory(document=d)

        row = self.row(locale=locale)

        eq_(row['title'], d.title)
        eq_(unicode(row['status']), u'Changes Needed')

    def test_needs_review(self):
        """Test status for article that needs review"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        d = TemplateDocumentFactory()
        RevisionFactory(document=d)

        row = self.row(locale=locale)

        eq_(row['title'], d.title)
        eq_(unicode(row['status']), u'Review Needed')

    def test_unready_for_l10n(self):
        """Test status for article that is not ready for l10n"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        d = TemplateDocumentFactory()
        RevisionFactory(document=d, is_ready_for_localization=True)
        ApprovedRevisionFactory(
            document=d, is_ready_for_localization=False, significance=MAJOR_SIGNIFICANCE)

        row = self.row(locale=locale)

        eq_(row['title'], d.title)
        eq_(unicode(row['status']), u'Changes Not Ready For Localization')


class HowToContributeTests(ReadoutTestCase):
    readout = HowToContributeReadout

    def test_only_how_to_contribute(self):
        """Test that only How To Contribute articles are shown"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        p = product(title='Firefox', slug='firefox', save=True)

        d1 = document(save=True)
        d2 = document(title='How To', category=HOW_TO_CONTRIBUTE_CATEGORY,
                      save=True)

        revision(document=d1, is_approved=True, save=True)
        revision(document=d2, is_approved=True, save=True)

        d1.products.add(p)
        d2.products.add(p)

        eq_(1, len(self.rows(locale=locale, product=p)))
        eq_(d2.title, self.row(locale=locale, product=p)['title'])
        eq_(u'', self.row(locale=locale, product=p)['status'])


class AdministrationTests(ReadoutTestCase):
    readout = AdministrationReadout

    def test_only_how_to_contribute(self):
        """Test that only Administration articles are shown"""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        p = product(title='Firefox', slug='firefox', save=True)

        d1 = document(save=True)
        d2 = document(title='Admin', category=ADMINISTRATION_CATEGORY,
                      save=True)

        revision(document=d1, is_approved=True, save=True)
        revision(document=d2, is_approved=True, save=True)

        d1.products.add(p)
        d2.products.add(p)

        eq_(1, len(self.rows(locale=locale, product=p)))
        eq_(d2.title, self.row(locale=locale, product=p)['title'])
        eq_(u'', self.row(locale=locale, product=p)['status'])


class MostVisitedTranslationsTests(ReadoutTestCase):
    """Tests for the Most Visited Translations readout

    This is an especially tricky readout, since it effectively implements a
    superset of all other readouts' status discriminators.

    """
    readout = MostVisitedTranslationsReadout

    def test_unreviewed(self):
        """Assert articles in need of review are labeled as such."""
        unreviewed = translated_revision(is_approved=False, save=True)
        row = self.row()
        eq_(row['title'], unreviewed.document.title)
        eq_(row['status'], 'Review Needed')

    def test_unlocalizable(self):
        """Unlocalizable docs shouldn't show up in the list."""
        revision(
            document=document(is_localizable=False, save=True),
            is_approved=True,
            save=True)
        self.assertRaises(IndexError, self.row)

    def _test_significance(self, significance, status):
        """
        Assert that a translation out of date due to a
        `significance`-level update to the original article shows
        status `status`.

        """
        translation = translated_revision(is_approved=True, save=True)
        revision(document=translation.document.parent,
                 is_approved=True,
                 is_ready_for_localization=True,
                 significance=significance,
                 save=True)
        row = self.row()
        eq_(row['title'], translation.document.title)
        eq_(row['status'], status)

    def test_out_of_date(self):
        """Assert out-of-date translations are labeled as such."""
        self._test_significance(MAJOR_SIGNIFICANCE, 'Immediate Update Needed')

    def test_update_needed(self):
        """Assert update-needed translations are labeled as such."""
        self._test_significance(MEDIUM_SIGNIFICANCE, 'Update Needed')

    def test_untranslated(self):
        """Assert untranslated documents are labeled as such."""
        untranslated = revision(is_approved=True,
                                is_ready_for_localization=True,
                                save=True)
        row = self.row()
        eq_(row['title'], untranslated.document.title)
        eq_(unicode(row['status']), 'Translation Needed')

    def test_up_to_date(self):
        """Show up-to-date translations have no status, just a happy class.
        """
        translation = translated_revision(is_approved=True, save=True)
        row = self.row()
        eq_(row['title'], translation.document.title)
        eq_(unicode(row['status']), '')
        eq_(row['status_class'], 'ok')

    def test_one_rejected_revision(self):
        """Translation with 1 rejected rev shows as Needs Translation"""
        translated_revision(is_approved=False,
                            reviewed=datetime.now(),
                            save=True)

        row = self.row()
        eq_(row['status_class'], 'untranslated')

    def test_spam(self):
        """Don't offer unapproved (often spam) articles for translation."""
        revision(is_approved=False, save=True)
        eq_([], MostVisitedTranslationsReadout(MockRequest()).rows())

    def test_consider_max_significance(self):
        """Use max significance for determining change significance

        When determining how significantly an article has changed
        since translation, use the max significance of the approved
        revisions, not just that of the latest ready-to-localize one.
        """
        translation = translated_revision(is_approved=True, save=True)
        revision(document=translation.document.parent,
                 is_approved=True,
                 is_ready_for_localization=False,  # should still count
                 significance=MAJOR_SIGNIFICANCE,
                 save=True)
        revision(document=translation.document.parent,
                 is_approved=True,
                 is_ready_for_localization=True,
                 significance=MEDIUM_SIGNIFICANCE,
                 save=True)
        row = self.row()
        eq_(row['title'], translation.document.title)
        eq_(unicode(row['status']), 'Immediate Update Needed')

    def test_consider_only_approved_significances(self):
        """Consider only approved significances when computing the max."""
        translation = translated_revision(is_approved=True, save=True)
        revision(document=translation.document.parent,
                 is_approved=False,  # shouldn't count
                 is_ready_for_localization=False,
                 significance=MAJOR_SIGNIFICANCE,
                 save=True)
        revision(document=translation.document.parent,
                 is_approved=True,
                 is_ready_for_localization=True,
                 significance=MEDIUM_SIGNIFICANCE,
                 save=True)
        row = self.row()
        eq_(row['title'], translation.document.title)
        # This should show as medium significance, because the revision with
        # major significance is unapproved:
        eq_(unicode(row['status']), 'Update Needed')

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = product(title='Firefox', slug='firefox', save=True)
        r = translated_revision(is_approved=True, save=True)
        d = r.document

        # There shouldn't be any rows yet.
        eq_(0, len(self.rows(product=p)))

        # Add the product to the parent document, and verify it shows up.
        d.parent.products.add(p)
        eq_(self.row(product=p)['title'], d.title)


class TemplateTranslationsTests(ReadoutTestCase):
    """Tests for the Template Translations readout"""

    readout = TemplateTranslationsReadout

    def test_not_template(self):
        """Documents that are not templates shouldn't show up in the list.
        """
        translated_revision(is_approved=False, save=True)
        self.assertRaises(IndexError, self.row)

    def test_untranslated(self):
        """Assert untranslated templates are labeled as such."""
        d = TemplateDocumentFactory()
        untranslated = ApprovedRevisionFactory(document=d, is_ready_for_localization=True)
        row = self.row()
        eq_(row['title'], untranslated.document.title)
        eq_(unicode(row['status']), 'Translation Needed')

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = product(title='Firefox', slug='firefox', save=True)
        d = TemplateDocumentFactory()
        ApprovedRevisionFactory(document=d, is_ready_for_localization=True)

        # There shouldn't be any rows yet.
        eq_(0, len(self.rows(product=p)))

        # Add the product to the document, and verify it shows up.
        d.products.add(p)
        eq_(self.row(product=p)['title'], d.title)


class UnreadyTests(ReadoutTestCase):
    """Tests for UnreadyForLocalizationReadout"""

    readout = UnreadyForLocalizationReadout

    def test_no_approved_revs(self):
        """Articles with no approved revisions should not appear."""
        revision(is_approved=False,
                 is_ready_for_localization=False,
                 significance=MAJOR_SIGNIFICANCE,
                 save=True)
        eq_([], self.titles())

    def test_unapproved_revs(self):
        """Don't show articles with unreviewed or rejected revs after latest
        """
        d = document(save=True)
        revision(document=d,
                 is_approved=True,
                 is_ready_for_localization=True,
                 save=True)
        revision(document=d,
                 is_approved=False,
                 reviewed=None,
                 is_ready_for_localization=False,
                 save=True)
        revision(document=d,
                 is_approved=False,
                 reviewed=datetime.now(),
                 is_ready_for_localization=False,
                 save=True)
        eq_([], self.titles())

    def test_first_rev(self):
        """If an article's first revision is approved, show the article.

        This also conveniently tests that documents with no
        latest_localizable_revision are not necessarily excluded.

        """
        r = revision(is_approved=True,
                     reviewed=datetime.now(),
                     is_ready_for_localization=False,
                     significance=None,
                     save=True)
        eq_([r.document.title], self.titles())

    def test_insignificant_revs(self):
        # Articles with approved, unready, but insignificant revisions
        # newer than their latest ready-for-l10n ones should not
        # appear.
        ready = revision(is_approved=True,
                         is_ready_for_localization=True,
                         save=True)
        revision(document=ready.document,
                 is_approved=True,
                 is_ready_for_localization=False,
                 significance=TYPO_SIGNIFICANCE,
                 save=True)
        eq_([], self.titles())

    def test_significant_revs(self):
        # Articles with approved, significant, but unready revisions
        # newer than their latest ready-for-l10n ones should appear.
        ready = revision(is_approved=True,
                         is_ready_for_localization=True,
                         save=True)
        revision(document=ready.document,
                 is_approved=True,
                 is_ready_for_localization=False,
                 significance=MEDIUM_SIGNIFICANCE,
                 save=True)
        eq_([ready.document.title], self.titles())

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = product(title='Firefox', slug='firefox', save=True)
        ready = revision(is_approved=True,
                         is_ready_for_localization=True,
                         save=True)
        revision(document=ready.document,
                 is_approved=True,
                 is_ready_for_localization=False,
                 significance=MEDIUM_SIGNIFICANCE,
                 save=True)

        # There shouldn't be any rows yet.
        eq_(0, len(self.rows(product=p)))

        # Add the product to the document, and verify it shows up.
        ready.document.products.add(p)
        eq_(self.row(product=p)['title'], ready.document.title)


class NeedsChangesTests(ReadoutTestCase):
    """Tests for the Needs Changes readout."""
    readout = NeedsChangesReadout

    def test_unrevieweds_after_current(self):
        """A document marked with needs_change=True should show up."""
        document = revision(save=True).document
        document.needs_change = True
        document.needs_change_comment = "Please update for Firefox.next"
        document.save()
        titles = self.titles()
        eq_(1, len(titles))
        assert document.title in titles

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = product(title='Firefox', slug='firefox', save=True)
        d = revision(save=True).document
        d.needs_change = True
        d.needs_change_comment = "Please update for Firefox.next"
        d.save()

        # There shouldn't be any rows yet.
        eq_(0, len(self.rows(product=p)))

        # Add the product to the document, and verify it shows up.
        d.products.add(p)
        eq_(self.row(product=p)['title'], d.title)


class CannedResponsesTests(ReadoutTestCase):
    readout = CannedResponsesReadout

    def test_canned(self):
        """Test the readout."""
        d = document(title='Foo', category=CANNED_RESPONSES_CATEGORY,
                     save=True)
        revision(is_approved=True,
                 is_ready_for_localization=True,
                 document=d,
                 save=True)

        eq_(1, len(self.rows()))

    def test_translation_state(self):
        eng_doc = document(category=CANNED_RESPONSES_CATEGORY, save=True)
        eng_rev = revision(is_approved=True, is_ready_for_localization=True,
                           document=eng_doc, save=True)

        eq_('untranslated', self.row()['status_class'])

        # Now translate it, but don't approve
        de_doc = document(category=CANNED_RESPONSES_CATEGORY, parent=eng_doc,
                          locale='de', save=True)
        de_rev = revision(is_approved=False, document=de_doc, based_on=eng_rev,
                          save=True)

        eq_('review', self.row()['status_class'])

        # Approve it, so now every this is ok.
        de_rev.is_approved = True
        de_rev.save()

        eq_('ok', self.row()['status_class'])

        # Now update the parent, so it becomes minorly out of date
        revision(is_approved=True, is_ready_for_localization=True,
                 document=eng_doc, significance=MEDIUM_SIGNIFICANCE,
                 save=True)

        eq_('update', self.row()['status_class'])

        # Now update the parent, so it becomes majorly out of date
        revision(is_approved=True, is_ready_for_localization=True,
                 document=eng_doc, significance=MAJOR_SIGNIFICANCE,
                 save=True)

        eq_('out-of-date', self.row()['status_class'])

    def test_by_product(self):
        """Test the product filtering of the readout."""
        p = product(title='Firefox', slug='firefox', save=True)
        d = document(title='Foo', category=CANNED_RESPONSES_CATEGORY,
                     save=True)
        revision(is_approved=True,
                 is_ready_for_localization=True,
                 document=d,
                 save=True)

        # There shouldn't be any rows yet.
        eq_(0, len(self.rows(product=p)))

        # Add the product to the document, and verify it shows up.
        d.products.add(p)
        eq_(1, len(self.rows(product=p)))
        eq_(self.row(product=p)['title'], d.title)
