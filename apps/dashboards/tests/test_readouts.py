from datetime import datetime

from nose.tools import eq_

from dashboards.readouts import (UnreviewedReadout, OutOfDateReadout,
                                 TemplateTranslationsReadout,
                                 MostVisitedTranslationsReadout)
from sumo.tests import TestCase
from wiki.models import MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE
from wiki.tests import revision, translated_revision, document


class MockRequest(object):
    locale = 'de'  # Same locale as translated_revision uses by default


class ReadoutTestCase(TestCase):
    """Test case for one readout. Provides some convenience methods."""

    def row(self):
        """Return first row shown by the readout this class tests."""
        return self.readout(MockRequest()).rows()[0]

    def titles(self):
        """Return the titles shown by the Unreviewed Changes readout."""
        return [row['title'] for row in
                self.readout(MockRequest()).rows()]


class UnreviewedChangesTests(ReadoutTestCase):
    """Tests for the Unreviewed Changes readout

    I'm not trying to cover every slice of the Venn diagram--just the tricky
    bits.

    """
    readout = UnreviewedReadout

    def test_unrevieweds_after_current(self):
        """Show the unreviewed revisions with later creation dates than the
        current"""
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
        """If there are reviewed but unapproved (i.e. rejected) revisions newer
        than the current_revision, don't show them."""
        rejected = translated_revision(reviewed=datetime.now(), save=True)
        assert rejected.document.title not in self.titles()


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
        """Assert that a translation out of date due to a `significance`-level
        update to the original article shows status `status`."""
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
        """Show up-to-date translations have no status, just a happy class."""
        translation = translated_revision(is_approved=True, save=True)
        row = self.row()
        eq_(row['title'], translation.document.title)
        eq_(unicode(row['status']), '')
        eq_(row['status_class'], 'ok')

    def test_spam(self):
        """Don't offer unapproved (often spam) articles for translation."""
        r = revision(is_approved=False, save=True)
        eq_([], MostVisitedTranslationsReadout(MockRequest()).rows())

    def test_consider_max_significance(self):
        """When determining how significantly an article has changed since
        translation, use the max significance of the approved revisions, not
        just that of the latest ready-to-localize one."""
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


class OutOfDateTests(ReadoutTestCase):
    """Tests for OutOfDateReadout and, by dint of factoring,
    NeedingUpdatesReadout."""

    readout = OutOfDateReadout

    def test_consider_max_significance(self):
        """When determining how significantly an article has changed since
        translation, use the max significance of the approved revisions, not
        just that of the latest ready-to-localize one."""
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
        eq_([translation.document.title], self.titles())


class TemplateTranslationsTests(ReadoutTestCase):
    """Tests for the Template Translations readout"""

    readout = TemplateTranslationsReadout

    def test_not_template(self):
        """Documents that are not templates shouldn't show up in the list."""
        translated_revision(is_approved=False, save=True)
        self.assertRaises(IndexError, self.row)

    def test_untranslated(self):
        """Assert untranslated templates are labeled as such."""
        d = document(title='Template:test', save=True)
        untranslated = revision(is_approved=True,
                                is_ready_for_localization=True,
                                document=d,
                                save=True)
        row = self.row()
        eq_(row['title'], untranslated.document.title)
        eq_(unicode(row['status']), 'Translation Needed')
