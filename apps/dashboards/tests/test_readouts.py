from datetime import datetime

from nose.tools import eq_

from dashboards.readouts import (UnreviewedReadout, OutOfDateReadout,
                                 TemplateTranslationsReadout, overview_rows,
                                 MostVisitedTranslationsReadout,
                                 UnreadyForLocalizationReadout,
                                 NeedsChangesReadout,
                                 NavigationTranslationsReadout,
                                 UntranslatedReadout)
from sumo.tests import TestCase
from wiki.config import (MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE,
                         TYPO_SIGNIFICANCE)
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


class OverviewTests(TestCase):
    """Tests for Overview readout"""
    def test_counting_unready_templates(self):
        """Templates without a ready-for-l10n rev shouldn't count in total."""
        # Make a template with an approved but not-ready-for-l10n rev:
        r = revision(document=document(title='Template:smoo',
                                       is_localizable=True,
                                       is_template=True,
                                       save=True),
                     is_ready_for_localization=False,
                     is_approved=True,
                     save=True)

        # It shouldn't show up in the total:
        eq_(0, overview_rows('de')['templates']['denominator'])

        r.is_ready_for_localization = True
        r.save()
        eq_(1, overview_rows('de')['templates']['denominator'])

    def test_counting_unready_navigation(self):
        """Navigation articles without ready-for-l10n rev shouldn't count in
        total.

        """
        # Make a navigation doc with an approved but not-ready-for-l10n rev:
        r = revision(document=document(title='smoo',
                                       category=50,
                                       is_localizable=True,
                                       is_template=False,
                                       save=True),
                     is_ready_for_localization=False,
                     is_approved=True,
                     save=True)

        # It shouldn't show up in the total:
        eq_(0, overview_rows('de')['navigation']['denominator'])

        r.is_ready_for_localization = True
        r.save()
        eq_(1, overview_rows('de')['navigation']['denominator'])

    def test_counting_unready_docs(self):
        """Docs without a ready-for-l10n rev shouldn't count in total."""
        # Make a doc with an approved but not-ready-for-l10n rev:
        r = revision(document=document(title='smoo',
                                       is_localizable=True,
                                       save=True),
                     is_ready_for_localization=False,
                     is_approved=True,
                     save=True)

        # It shouldn't show up in the total:
        eq_(0, overview_rows('de')['all']['denominator'])

        r.is_ready_for_localization = True
        r.save()
        eq_(1, overview_rows('de')['all']['denominator'])

    def test_counting_unready_parents(self):
        """Translations whose parents have no ready-to-localize revisions
        should not count in the numerator.

        By dint of factoring, this also tests that templates whose parents....

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
        eq_(0, overview_rows('de')['all']['numerator'])

    def test_templates_and_docs_disjunct(self):
        """Make sure templates aren't included in the All Articles count."""
        t = translated_revision(is_approved=True, save=True)
        # It shows up in All when it's a normal doc:
        eq_(1, overview_rows('de')['all']['numerator'])
        eq_(1, overview_rows('de')['all']['denominator'])

        t.document.parent.title = t.document.title = 'Template:thing'
        t.document.parent.is_template = t.document.is_template = True
        t.document.parent.save()
        t.document.save()
        # ...but not when it's a template:
        eq_(0, overview_rows('de')['all']['numerator'])
        eq_(0, overview_rows('de')['all']['denominator'])

    def test_all_articles_doesnt_have_30_40_50(self):
        """Make sure All Articles doesn't have 30, 40, and 50 articles"""
        t = translated_revision(is_approved=True, save=True)
        # It shows up in All when it's a normal doc:
        eq_(1, overview_rows('de')['all']['numerator'])
        eq_(1, overview_rows('de')['all']['denominator'])

        # ...but not when it's a navigation article:
        t.document.parent.title = t.document.title = 'thing'
        t.document.parent.category = t.document.category = 50
        t.document.parent.save()
        t.document.save()
        eq_(0, overview_rows('de')['all']['numerator'])
        eq_(0, overview_rows('de')['all']['denominator'])

        # ...or administration:
        t.document.parent.category = t.document.category = 40
        t.document.parent.save()
        t.document.save()
        eq_(0, overview_rows('de')['all']['numerator'])
        eq_(0, overview_rows('de')['all']['denominator'])

        # ...or how to contribute:
        t.document.parent.category = t.document.category = 30
        t.document.parent.save()
        t.document.save()
        eq_(0, overview_rows('de')['all']['numerator'])
        eq_(0, overview_rows('de')['all']['denominator'])

    def test_not_counting_outdated(self):
        """Out-of-date translations shouldn't count as "done".

        "Out-of-date" can mean either moderately or majorly out of date. The
        only thing we don't care about is typo-level outdatedness.

        """
        t = translated_revision(is_approved=True, save=True)
        overview = overview_rows('de')
        eq_(1, overview['most-visited']['numerator'])
        eq_(1, overview['all']['numerator'])

        # Update the parent with a typo-level revision:
        revision(document=t.document.parent,
                 significance=TYPO_SIGNIFICANCE,
                 is_approved=True,
                 is_ready_for_localization=True,
                 save=True)
        # Assert it still shows up in the numerators:
        overview = overview_rows('de')
        eq_(1, overview['most-visited']['numerator'])
        eq_(1, overview['all']['numerator'])

        # Update the parent with a medium-level revision:
        revision(document=t.document.parent,
                 significance=MEDIUM_SIGNIFICANCE,
                 is_approved=True,
                 is_ready_for_localization=True,
                 save=True)
        # Assert it no longer shows up in the numerators:
        overview = overview_rows('de')
        eq_(0, overview['all']['numerator'])
        eq_(0, overview['most-visited']['numerator'])

    def test_not_counting_untranslated(self):
        """Translations with no approved revisions shouldn't count as done."""
        t = translated_revision(is_approved=False, save=True)
        overview = overview_rows('de')
        eq_(0, overview['most-visited']['numerator'])
        eq_(0, overview['all']['numerator'])


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

    def test_one_rejected_revision(self):
        """A translation with only 1 revision, which is rejected, should show
        as "Needs Translation".

        """
        translated_revision(is_approved=False,
                            reviewed=datetime.now(),
                            save=True)

        row = self.row()
        eq_(row['status_class'], 'untranslated')

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


class NavigationTranslationsTests(ReadoutTestCase):
    """Tests for the Navigation Translations readout"""

    readout = NavigationTranslationsReadout

    def test_not_navigation(self):
        """Documents not in navigation shouldn't show up in the list."""
        t = translated_revision(is_approved=False, save=True)
        t.document.category = 10
        t.document.save()

        t = translated_revision(is_approved=False, save=True)
        t.document.category = 20
        t.document.save()

        t = translated_revision(is_approved=False, save=True)
        t.document.category = 30
        t.document.save()

        t = translated_revision(is_approved=False, save=True)
        t.document.category = 40
        t.document.save()

        t = translated_revision(is_approved=False, save=True)
        t.document.category = 60
        t.document.save()

        self.assertRaises(IndexError, self.row)

    def test_untranslated(self):
        """Assert untranslated navigation are labeled as such."""
        d = document(title='Foo', category=50, save=True)
        untranslated = revision(is_approved=True,
                                is_ready_for_localization=True,
                                document=d,
                                save=True)
        row = self.row()
        eq_(row['title'], untranslated.document.title)
        eq_(unicode(row['status']), u'Translation Needed')


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
        """Articles with only unreviewed or rejected revs after the latest
        ready one should not appear."""
        d = document(save=True)
        ready = revision(document=d,
                         is_approved=True,
                         is_ready_for_localization=True,
                         save=True)
        unreviewed = revision(document=d,
                              is_approved=False,
                              reviewed=None,
                              is_ready_for_localization=False,
                              save=True)
        rejected = revision(document=d,
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
        """Articles with approved, unready, but insignificant revisions newer
        than their latest ready-for-l10n ones should not appear."""
        ready = revision(is_approved=True,
                         is_ready_for_localization=True,
                         save=True)
        insignificant = revision(document=ready.document,
                                 is_approved=True,
                                 is_ready_for_localization=False,
                                 significance=TYPO_SIGNIFICANCE,
                                 save=True)
        eq_([], self.titles())

    def test_significant_revs(self):
        """Articles with approved, significant, but unready revisions newer
        than their latest ready-for-l10n ones should appear."""
        ready = revision(is_approved=True,
                         is_ready_for_localization=True,
                         save=True)
        significant = revision(document=ready.document,
                               is_approved=True,
                               is_ready_for_localization=False,
                               significance=MEDIUM_SIGNIFICANCE,
                               save=True)
        eq_([ready.document.title], self.titles())


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


class UntranslatedTests(ReadoutTestCase):
    """Tests for the Untranslated readout"""
    readout = UntranslatedReadout

    def test_redirects_not_shown(self):
        """Redirects shouldn't appear in Untranslated readout."""
        revision(is_approved=True, is_ready_for_localization=True,
                 content='REDIRECT [[Foo Bar]]', save=True)

        eq_(0, len(self.titles()))
