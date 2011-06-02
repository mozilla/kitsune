from datetime import datetime

from nose.tools import eq_

from dashboards.readouts import (UnreviewedReadout,
                                 TemplateTranslationsReadout,
                                 MostVisitedTranslationsReadout)
from sumo.tests import TestCase
from wiki.models import MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE
from wiki.tests import revision, translated_revision, document


class MockRequest(object):
    locale = 'de'  # Same locale as translated_revision uses by default


class UnreviewedChangesTests(TestCase):
    """Tests for the Unreviewed Changes readout

    I'm not trying to cover every slice of the Venn diagram--just the tricky
    bits.

    """
    @staticmethod
    def titles():
        """Return the titles shown by the Unreviewed Changes readout."""
        return [row['title'] for row in
                UnreviewedReadout(MockRequest()).rows()]

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


class MostVisitedTranslationsTests(TestCase):
    """Tests for the Most Visited Translations readout

    This is an especially tricky readout, since it effectively implements a
    superset of all other readouts' status discriminators.

    """
    @staticmethod
    def row():
        """Return first row shown by the Most Visited Translations readout."""
        return MostVisitedTranslationsReadout(MockRequest()).rows()[0]

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
                 significance=significance, save=True)
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
        untranslated = revision(save=True, is_approved=True)
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


class TemplateTranslationsReadoutTests(TestCase):
    """Tests for the Template Translations readout"""

    @staticmethod
    def row():
        """Return first row shown by the Template Translations readout."""
        return TemplateTranslationsReadout(MockRequest()).rows()[0]

    def test_not_template(self):
        """Documents that are not templates shouldn't show up in the list."""
        translated_revision(is_approved=False, save=True)
        self.assertRaises(IndexError, self.row)

    def test_untranslated(self):
        """Assert untranslated templates are labeled as such."""
        d = document(title='Template:test', save=True)
        untranslated = revision(is_approved=True, document=d, save=True)
        row = self.row()
        eq_(row['title'], untranslated.document.title)
        eq_(unicode(row['status']), 'Translation Needed')
