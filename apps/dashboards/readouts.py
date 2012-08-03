"""Data aggregators for dashboards

For the purposes of all these numbers, we pretend as if Documents with
is_localizable=False or is_archived=True and Revisions with
is_ready_for_localization=False do not exist.

"""
import logging

from django.conf import settings
from django.db import connections, router
from django.utils.datastructures import SortedDict

import jingo
from jinja2 import Markup
from tower import ugettext as _, ugettext_lazy as _lazy

from dashboards import LAST_30_DAYS, PERIODS
from sumo.urlresolvers import reverse
from sumo.redis_utils import redis_client, RedisError
from wiki.models import Document
from wiki.config import (MEDIUM_SIGNIFICANCE, MAJOR_SIGNIFICANCE,
                         TYPO_SIGNIFICANCE)


log = logging.getLogger('k.dashboards.readouts')


MOST_VIEWED = 1
MOST_RECENT = 2


# FROM clause for selecting most-visited translations:
#
# The "... EXISTS" bit in the transdoc left join prevents transdocs
# for which there are only translated revisions that were reviewed and
# rejected. In this case, we want it to show up as untranslated since
# that's the most "correct" status.
most_visited_translation_from = (
    'FROM wiki_document engdoc '
    'LEFT JOIN wiki_document transdoc ON '
        'transdoc.parent_id=engdoc.id '
        'AND transdoc.locale=%s '
        'AND EXISTS ('
            'SELECT * '
            'FROM wiki_revision transrev_inner '
            'WHERE transrev_inner.document_id=transdoc.id '
            'AND NOT (NOT transrev_inner.is_approved '
                     'AND transrev_inner.reviewed IS NOT NULL) '
        ') '
    'LEFT JOIN dashboards_wikidocumentvisits ON engdoc.id='
        'dashboards_wikidocumentvisits.document_id '
        'AND dashboards_wikidocumentvisits.period=%s '
    '{extra_joins} '
    'WHERE engdoc.locale=%s '
        'AND engdoc.is_localizable '
        'AND NOT engdoc.is_archived '
        'AND engdoc.latest_localizable_revision_id IS NOT NULL '
    'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
             'COALESCE(transdoc.title, engdoc.title) ASC ').format


REVIEW_STATUSES = {
    1: (_lazy(u'Review Needed'), 'wiki.document_revisions', 'review'),
    0: (u'', '', 'ok')}
SIGNIFICANCE_STATUSES = {
    MEDIUM_SIGNIFICANCE:
        (_lazy(u'Update Needed'), 'wiki.edit_document', 'update'),
    MAJOR_SIGNIFICANCE:
        (_lazy(u'Immediate Update Needed'), 'wiki.edit_document',
         'out-of-date')}

# The most significant approved change to the English article between {the
# English revision the current translated revision is based on} and {the latest
# ready-for-localization revision}:
MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE = (
    '(SELECT MAX(engrev.significance) '
     'FROM wiki_revision engrev, wiki_revision transrev '
     'WHERE engrev.is_approved '
     'AND transrev.id=transdoc.current_revision_id '
     'AND engrev.document_id=transdoc.parent_id '
     'AND engrev.id>transrev.based_on_id '
     'AND engrev.id<=engdoc.latest_localizable_revision_id'
    ')')

# Whether there are any unreviewed revs of the translation made since the
# current one:
NEEDS_REVIEW = (
    '(SELECT EXISTS '
        '(SELECT * '
         'FROM wiki_revision transrev '
         'WHERE transrev.document_id=transdoc.id '
         'AND transrev.reviewed IS NULL '
         'AND (transrev.id>transdoc.current_revision_id OR '
              'transdoc.current_revision_id IS NULL)'
        ')'
    ') ')

# Any ready-for-l10n, nontrivial-significance revision of the English doc newer
# than the one our current translation is based on:
ANY_SIGNIFICANT_UPDATES = (
    '(SELECT id FROM wiki_revision engrev '
     'WHERE engrev.document_id=engdoc.id '
     'AND engrev.id>curtransrev.based_on_id '
     'AND engrev.is_ready_for_localization '
     'AND engrev.significance>=%s) ')


def _cursor():
    """Return a DB cursor for reading."""
    return connections[router.db_for_read(Document)].cursor()


def _format_row_with_out_of_dateness(readout_locale, eng_slug, eng_title, slug,
                                    title, visits, significance, needs_review):
    """Format a row for a readout that has the traffic-light-style
    categorization of how seriously out of date a translation is."""
    if slug:  # A translation exists but may not be approved.
        locale = readout_locale
        status, view_name, status_class = SIGNIFICANCE_STATUSES.get(
            significance, REVIEW_STATUSES[needs_review])
        status_url = (reverse(view_name, args=[slug], locale=locale)
                      if view_name else '')
    else:
        slug = eng_slug
        title = eng_title
        locale = settings.WIKI_DEFAULT_LANGUAGE
        status = _(u'Translation Needed')
        # When calling the translate view, specify locale to translate to:
        status_url = reverse('wiki.translate', args=[slug],
                             locale=readout_locale)
        status_class = 'untranslated'

    return dict(title=title,
                url=reverse('wiki.document', args=[slug],
                            locale=locale),
                visits=visits,
                status=status,
                status_class=status_class,
                status_url=status_url)


def overview_rows(locale):
    """Return the iterable of dicts needed to draw the Overview table."""
    # The Overview table is a special case: it has only a static number of
    # rows, so it has no expanded, all-rows view, and thus needs no slug, no
    # "max" kwarg on rows(), etc. It doesn't fit the Readout signature, so we
    # don't shoehorn it in.

    def percent_or_100(num, denom):
        return int(round(num / float(denom) * 100)) if denom else 100

    def single_result(sql, params):
        """Return the first column of the first row returned by a query."""
        cursor = _cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()[0]

    total = Document.uncached.filter(
        locale=settings.WIKI_DEFAULT_LANGUAGE,
        is_archived=False,
        current_revision__isnull=False,
        is_localizable=True,
        latest_localizable_revision__isnull=False)
    total_docs = (total.filter(is_template=False)
                  .filter(category__in=(10, 20, 60))
                  .count())
    total_navigation = (total.filter(is_template=False)
                        .filter(category=50)
                        .count())
    total_templates = total.filter(is_template=True).count()

    # Translations whose based_on revision has no >10-significance, ready-for-
    # l10n revisions after it. It *might* be possible to do this with the ORM
    # by passing wheres and tables to extra():
    up_to_date_translation_count = (
        'SELECT COUNT(*) FROM wiki_document transdoc '
        'INNER JOIN wiki_document engdoc ON transdoc.parent_id=engdoc.id '
        'INNER JOIN wiki_revision curtransrev '
            'ON transdoc.current_revision_id=curtransrev.id '
        'WHERE transdoc.locale=%s '
            'AND transdoc.is_template=%s '
            'AND NOT transdoc.is_archived '
            'AND engdoc.latest_localizable_revision_id IS NOT NULL '
            'AND engdoc.is_localizable '
            'AND NOT EXISTS ' +
                ANY_SIGNIFICANT_UPDATES)
    translated_docs = single_result(
        up_to_date_translation_count +
        'AND transdoc.category in (10, 20, 60)',
        (locale, False, MEDIUM_SIGNIFICANCE))
    translated_navigation = single_result(
        up_to_date_translation_count +
        'AND transdoc.category = 50',
        (locale, False, MEDIUM_SIGNIFICANCE))
    translated_templates = single_result(
        up_to_date_translation_count,
        (locale, True, MEDIUM_SIGNIFICANCE))

    # Of the top 20 most visited English articles, how many have up-to-date
    # translations into German?
    #
    # TODO: Be very suspicious of this query. It selects from a subquery (known
    # to MySQL's EXPLAIN as a "derived" table), and MySQL always materializes
    # such subqueries and never builds indexes on them. However, it seems to be
    # fast in practice.
    TOP_N = 20
    popular_translated = int(single_result(  # Driver returns a Decimal.
        'SELECT SUM(istranslated) FROM '
            '(SELECT transdoc.current_revision_id IS NOT NULL '
                # And there have been no significant updates since the current
                # translation:
                'AND NOT EXISTS ' +
                ANY_SIGNIFICANT_UPDATES +
                'AS istranslated ' +
             most_visited_translation_from(extra_joins=
                'LEFT JOIN wiki_revision curtransrev '
                    'ON transdoc.current_revision_id=curtransrev.id ') +
             'LIMIT %s) t1 ',
        (MEDIUM_SIGNIFICANCE, locale, LAST_30_DAYS,
         settings.WIKI_DEFAULT_LANGUAGE, TOP_N)) or 0)  # SUM can return NULL.

    return {'most-visited': dict(
                 title=_('Most-Visited Articles'),
                 url='#' + MostVisitedTranslationsReadout.slug,
                 numerator=popular_translated, denominator=TOP_N,
                 percent=percent_or_100(popular_translated, TOP_N),
                 description=_('These are the top 20 most visited articles, '
                               'which account for over 50% of the traffic to '
                               'the Knowledge Base.')),
            'templates': dict(
                 title=_('Templates'),
                 url='#' + TemplateTranslationsReadout.slug,
                 numerator=translated_templates, denominator=total_templates,
                 percent=percent_or_100(translated_templates, total_templates),
                 description=_('Templates are a way of reusing pieces of '
                               'content across KB articles. You can create and '
                               'update a set of instructions in one place, and '
                               'then refer to it in other pages.')),
            'navigation': dict(
                 title=_('Navigation Articles'),
                 url='#' + NavigationTranslationsReadout.slug,
                 numerator=translated_navigation, denominator=total_navigation,
                 percent=percent_or_100(translated_navigation, total_navigation),
                 description=_('How many of the approved navigation articles '
                               'which allow translations have an approved '
                               'translation into this language')),
            'all': dict(
                 title=_('All Knowledge Base Articles'),
                 numerator=translated_docs, denominator=total_docs,
                 percent=percent_or_100(translated_docs, total_docs),
                 description=_('This is the number of all Knowledge Base '
                               'articles that are ready to be localized.'))}


class Readout(object):
    """Abstract class representing one table on the Localization Dashboard

    Describing these as atoms gives us the whole-page details views for free.

    """
    # title = _lazy(u'Title of Readout')
    # description = _lazy(u'Paragraph of explanation')
    # short_title= = _lazy(u'Short Title of Readout for In-Page Links')
    # slug = 'Unique URL slug for detail page'
    # details_link_text = _lazy(u'All articles from this readout...')
    column3_label = _lazy(u'Visits in last 30 days')
    column4_label = _lazy(u'Status')
    modes = [(MOST_VIEWED, _lazy('Most Viewed')),
             (MOST_RECENT, _lazy('Most Recent'))]
    default_mode = MOST_VIEWED

    def __init__(self, request, locale=None, mode=None):
        """Take request so the template can use contextual macros that need it.

        Renders the data for the locale specified by the request, but you can
        override it by passing another in `locale`.

        """
        self.request = request
        self.locale = locale or request.locale
        self.mode = mode if mode != None else self.default_mode
        # self.mode is allowed to be invalid.

    def sort_and_truncate(self, rows, max):
        """Allows a readout to sort and truncate the rows list

        This happens after generating the row structures which starts
        with what we get back from SQL and incorporates _format_row
        and before we render the rows to output.

        :arg rows: the list of rows to sort
        :arg max: the index at which to truncate
        """
        return rows

    def rows(self, max=None):
        """Return an iterable of dicts containing the data for the table.

        This default implementation calls _query_and_params and _format_row.
        You can either implement those or, if you need more flexibility,
        override this.

        Limit to `max` rows.

        """
        cursor = _cursor()
        cursor.execute(*self._query_and_params(max))
        return self.sort_and_truncate(
            [self._format_row(r) for r in cursor.fetchall()], max)

    def render(self, max_rows=None):
        """Return HTML table rows, optionally limiting to a number of rows."""
        # Compute percents for bar widths:
        rows = self.rows(max_rows)
        max_visits = max(r['visits'] for r in rows) if rows else 0
        for r in rows:
            visits = r['visits']
            r['percent'] = (0 if visits is None or not max_visits
                            else int(round(visits / float(max_visits) * 100)))

        # Render:
        return jingo.render_to_string(
            self.request,
            'dashboards/includes/kb_readout.html',
            {'rows': rows, 'column3_label': self.column3_label,
             'column4_label': self.column4_label})

    @staticmethod
    def should_show_to(user):
        """Whether this readout should be shown to the user"""
        return True

    # To override:

    def _query_and_params(self, max):
        """Return a tuple: (query, params to bind it to)."""
        raise NotImplementedError

    def _format_row(self, row):
        """Turn a DB row tuple into a dict for the template."""
        raise NotImplementedError

    # Convenience methods:

    @staticmethod
    def _limit_clause(max):
        """Return a SQL LIMIT clause limiting returned rows to `max`.

        Return '' if max is None.

        """
        return ' LIMIT %i' % max if max else ''

    def get_absolute_url(self, locale):
        if self.slug in L10N_READOUTS:
            return reverse('dashboards.localization_detail',
                           kwargs={'readout_slug': self.slug}, locale=locale)
        elif self.slug in CONTRIBUTOR_READOUTS:
            return reverse('dashboards.contributors_detail',
                           kwargs={'readout_slug': self.slug}, locale=locale)
        else:
            raise KeyError('This Readout was not found: %s' % self.slug)


class MostVisitedDefaultLanguageReadout(Readout):
    """Most-Visited readout for the default language"""
    title = _lazy(u'Most Visited')
    # No short_title; the Contributors dash lacks an Overview readout
    details_link_text = _lazy(u'All knowledge base articles...')
    slug = 'most-visited'
    column3_label = _lazy(u'Visits')
    modes = PERIODS
    default_mode = LAST_30_DAYS

    def _query_and_params(self, max):
        if self.mode in [m[0] for m in self.modes]:
            period = self.mode
        else:
            period = self.default_mode
        # Review Needed: link to /history.
        return ('SELECT engdoc.slug, engdoc.title, '
                'dashboards_wikidocumentvisits.visits, '
                'count(engrev.document_id) '
                'FROM wiki_document engdoc '
                'LEFT JOIN dashboards_wikidocumentvisits ON '
                    'engdoc.id=dashboards_wikidocumentvisits.document_id '
                    'AND dashboards_wikidocumentvisits.period=%s '
                'LEFT JOIN wiki_revision engrev ON '
                    'engrev.document_id=engdoc.id '
                    'AND engrev.reviewed IS NULL '
                    'AND engrev.id>engdoc.current_revision_id '
                'WHERE engdoc.locale=%s AND '
                    'NOT engdoc.is_archived '
                'GROUP BY engdoc.id '
                'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
                         'engdoc.title ASC' + self._limit_clause(max),
            (period, self.locale))

    def _format_row(self, (slug, title, visits, num_unreviewed)):
        needs_review = int(num_unreviewed > 0)
        status, view_name, dummy = REVIEW_STATUSES[needs_review]
        return dict(title=title,
                    url=reverse('wiki.document', args=[slug],
                                locale=self.locale),
                    visits=visits,
                    status=status,
                    status_url=reverse(view_name, args=[slug],
                                       locale=self.locale)
                               if view_name else '')


class MostVisitedTranslationsReadout(MostVisitedDefaultLanguageReadout):
    """Most-Visited readout for non-default languages

    Adds a few subqueries to determine the status of translations.

    Shows the articles that are most visited in English, even if there are no
    translations of those articles yet. This draws attention to articles that
    we should drop everything to translate.

    """
    # No short_title; the link to this one is hard-coded in Overview readout
    slug = 'most-visited-translations'
    details_link_text = _lazy(u'All translations...')

    def _query_and_params(self, max):
        if self.mode in [m[0] for m in self.modes]:
            period = self.mode
        else:
            period = self.default_mode
        # Immediate Update Needed or Update Needed: link to /edit.
        # Review Needed: link to /history.
        # These match the behavior of the corresponding readouts.
        return (
            'SELECT engdoc.slug, engdoc.title, transdoc.slug, '
            'transdoc.title, dashboards_wikidocumentvisits.visits, ' +
            MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE + ', ' +
            NEEDS_REVIEW +
            most_visited_translation_from(extra_joins='') +
            self._limit_clause(max),
            (self.locale, period, settings.WIKI_DEFAULT_LANGUAGE))

    def _format_row(self, columns):
        return _format_row_with_out_of_dateness(self.locale, *columns)


class TemplateTranslationsReadout(Readout):
    """Readout for templates in non-default languages

    Shows the templates even if there are no translations of them yet.
    This draws attention to templates that we should drop everything to
    translate.

    """
    title = _lazy(u'Templates')
    slug = 'template-translations'
    details_link_text = _lazy(u'All templates...')
    column3_label = ''
    modes = []
    default_mode = None

    def _query_and_params(self, max):
        return (
            'SELECT engdoc.slug, engdoc.title, transdoc.slug, '
            'transdoc.title, ' +
            MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE + ', ' +
            NEEDS_REVIEW +

            'FROM wiki_document engdoc '
            'LEFT JOIN wiki_document transdoc ON '
                'transdoc.parent_id=engdoc.id '
                'AND transdoc.locale=%s '
            'WHERE engdoc.locale=%s '
                'AND engdoc.is_localizable '
                'AND NOT engdoc.is_archived '
                'AND engdoc.latest_localizable_revision_id IS NOT NULL '
                'AND engdoc.is_template ',
            (self.locale, settings.WIKI_DEFAULT_LANGUAGE))

    def _format_row(self, (eng_slug, eng_title, slug, title, significance,
                           needs_review)):
        return _format_row_with_out_of_dateness(self.locale, eng_slug,
            eng_title, slug, title, None, significance, needs_review)

    def sort_and_truncate(self, rows, max):
        # Bubble the "update needed" templates to the top, but otherwise
        # keep it ordered by title.
        #
        # As a little side note, 'status' here is either an empty
        # string or a _lazy translation of 'Update Needed'. So if it's
        # an empty string, then the equality is True and True in
        # Python is 1 and 1 comes after 0... Therefore, False comes
        # first in ordering.
        rows.sort(key=lambda row: (
                row['status'] == u'', row['status_class'], row['title']))
        return rows[:max]


class NavigationTranslationsReadout(Readout):
    """Readout for navigation articles in non-default languages

    Shows the navigation articles even if there are no translations of
    them yet.  This draws attention to navigation articles that we
    should drop everything to translate.

    """
    title = _lazy(u'Navigation Articles')
    slug = 'template-navigation'
    details_link_text = _lazy(u'All navigation articles...')
    column3_label = ''
    modes = []
    default_mode = None

    def _query_and_params(self, max):
        return (
            'SELECT engdoc.slug, engdoc.title, transdoc.slug, '
            'transdoc.title, ' +
            MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE + ', ' +
            NEEDS_REVIEW +

            'FROM wiki_document engdoc '
            'LEFT JOIN wiki_document transdoc ON '
                'transdoc.parent_id=engdoc.id '
                'AND transdoc.locale=%s '
            'WHERE engdoc.locale=%s '
                'AND engdoc.is_localizable '
                'AND NOT engdoc.is_archived '
                'AND engdoc.latest_localizable_revision_id IS NOT NULL '
                'AND engdoc.category = 50 '
                'AND NOT engdoc.is_template '
            'ORDER BY COALESCE(transdoc.title, engdoc.title) ASC ' +

            self._limit_clause(max),
            (self.locale, settings.WIKI_DEFAULT_LANGUAGE))

    def _format_row(self, (eng_slug, eng_title, slug, title, significance,
                           needs_review)):
        return _format_row_with_out_of_dateness(self.locale, eng_slug,
            eng_title, slug, title, None, significance, needs_review)


class UntranslatedReadout(Readout):
    title = _lazy(u'Untranslated')
    short_title = _lazy(u'Untranslated')
    details_link_text = _lazy(u'All untranslated articles...')
    slug = 'untranslated'
    column4_label = _lazy(u'Updated')

    def _query_and_params(self, max):
        # Incidentally, we tried this both as a left join and as a search
        # against an inner query returning translated docs, and the left join
        # yielded a faster-looking plan (on a production corpus).
        #
        # Find non-archived, localizable documents in categories 10,
        # 20 and 60 having at least one ready- for-localization
        # revision. Of those, show the ones that have no translation.
        return ('SELECT parent.slug, parent.title, '
            'wiki_revision.reviewed, dashboards_wikidocumentvisits.visits '
            'FROM wiki_document parent '
            'INNER JOIN wiki_revision ON '
                'parent.latest_localizable_revision_id=wiki_revision.id '
            'LEFT JOIN wiki_document translated ON '
                'parent.id=translated.parent_id AND translated.locale=%s '
            'LEFT JOIN dashboards_wikidocumentvisits ON '
                'parent.id=dashboards_wikidocumentvisits.document_id AND '
                'dashboards_wikidocumentvisits.period=%s '
            'WHERE '
            'translated.id IS NULL AND parent.is_localizable AND '
            'parent.category in (10, 20, 60) AND '
            'parent.locale=%s AND NOT parent.is_archived '
            'AND wiki_revision.content NOT LIKE "REDIRECT%%" '
            + self._order_clause() + self._limit_clause(max),
            (self.locale, LAST_30_DAYS, settings.WIKI_DEFAULT_LANGUAGE))

    def _order_clause(self):
        return ('ORDER BY wiki_revision.reviewed DESC, parent.title ASC'
                if self.mode == MOST_RECENT
                else 'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
                     'parent.title ASC')

    def _format_row(self, (slug, title, reviewed, visits)):
        # Run the data through the model to (potentially) format it and
        # take advantage of SPOTs (like for get_absolute_url()):
        d = Document(slug=slug, title=title,
                     locale=settings.WIKI_DEFAULT_LANGUAGE)
        return dict(title=d.title,
                    url=d.get_absolute_url(),
                    visits=visits,
                    updated=reviewed)


class OutOfDateReadout(Readout):
    title = _lazy(u'Immediate Updates Needed')
    description = _lazy(
        u'This indicates a major edit which changes the content of the article'
         ' enough to hurt the value of the localization. Until it is updated, '
         'the localized page will warn users that it may be outdated. You '
         'should update these articles as soon as possible.')
    short_title = _lazy(u'Immediate Updates Needed')
    details_link_text = _lazy(u'All translations needing immediate updates...')
    slug = 'out-of-date'
    column4_label = _lazy(u'Out of date since')

    # To show up in this readout, an article's revision since the last
    # approved translation must have a maximum significance equal to this
    # value:
    _max_significance = MAJOR_SIGNIFICANCE

    def _query_and_params(self, max):
        # At the moment, the "Out of Date Since" column shows the time since
        # the translation was out of date at a MEDIUM level of severity or
        # higher. We could arguably knock this up to MAJOR, but technically it
        # is out of date when the original gets anything more than typo
        # corrections.
        return ('SELECT transdoc.slug, transdoc.title, engrev.reviewed, '
            'dashboards_wikidocumentvisits.visits '
            'FROM wiki_document transdoc '
            'INNER JOIN wiki_document engdoc ON transdoc.parent_id=engdoc.id '
            'INNER JOIN wiki_revision engrev ON engrev.id='
            # The oldest English rev to have an approved, ready-for-
            # localization level-30 change since the translated doc had an
            # approved rev based on it. NULL if there is none:
                '(SELECT min(id) FROM wiki_revision '
                # Narrow engrev rows to those representing revision of parent
                # doc:
                'WHERE wiki_revision.document_id=transdoc.parent_id '
                # For the purposes of computing the "Out of Date Since" column,
                # the revision that threw the translation out of date had
                # better be more recent than the one the current translation is
                # based on:
                'AND wiki_revision.id>'
                    '(SELECT based_on_id FROM wiki_revision basedonrev '
                    'WHERE basedonrev.id=transdoc.current_revision_id) '
                'AND wiki_revision.significance>=%s '
                'AND %s='
                # Completely filter out outer selections where 30 is not the
                # max signif of approved English revisions since trans was last
                # approved. Other maxes will be shown by other readouts.
                # Optimize: try "30 IN" if MySQL's statistics gatherer is
                # stupid/nonexistent; the inner query should be able to bail
                # out early. [Ed: No effect on EXPLAIN on admittedly light test
                # corpus.]
                  '(SELECT MAX(engsince.significance) '
                   'FROM wiki_revision engsince '
                   'WHERE engsince.document_id=transdoc.parent_id '
                   # Assumes that any approved revision became the current
                   # revision at some point: we don't let the user go back and
                   # approve revisions older than the latest approved one.
                   'AND engsince.is_approved '
                   # Consider revisions between the one the last translation
                   # was based on and the latest ready-for-l10n one.
                   'AND engsince.id>'
                   # The English revision the current translation's based on:
                     '(SELECT based_on_id FROM wiki_revision basedonrev '
                     'WHERE basedonrev.id=transdoc.current_revision_id) '
                   'AND engsince.id<=engdoc.latest_localizable_revision_id'
                  ')'
                ') '
            # Join up the visits table for stats:
            'LEFT JOIN dashboards_wikidocumentvisits ON '
                'engrev.document_id=dashboards_wikidocumentvisits.document_id '
                'AND dashboards_wikidocumentvisits.period=%s '
            # We needn't check is_localizable, since the models ensure every
            # document with translations has is_localizable set.
            'WHERE transdoc.locale=%s AND NOT transdoc.is_archived AND '
                'transdoc.category in (10, 20, 60) '
            + self._order_clause() + self._limit_clause(max),
            (MEDIUM_SIGNIFICANCE, self._max_significance, LAST_30_DAYS,
                self.locale))

    def _order_clause(self):
        return ('ORDER BY engrev.reviewed DESC' if self.mode == MOST_RECENT
                else 'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
                     'transdoc.title ASC')

    def _format_row(self, (slug, title, reviewed, visits)):
        return dict(title=title,
                    url=reverse('wiki.edit_document', args=[slug]),
                    visits=visits, updated=reviewed)


class NeedingUpdatesReadout(OutOfDateReadout):
    title = _lazy(u'Updates Needed')
    description = _lazy(
        u"This signifies an edit that doesn't diminish the value of the "
         'localized article: for example, rewording a paragraph. Localizers '
         'are notified of this edit, but no warning is shown on the localized '
         'page. You should update these articles soon.')
    short_title = _lazy(u'Updates Needed')
    details_link_text = _lazy(u'All translations needing updates...')
    slug = 'needing-updates'

    _max_significance = MEDIUM_SIGNIFICANCE


class UnreviewedReadout(Readout):
    # L10n: Not just changes to translations but also unreviewed changes to
    # docs in this locale that are not translations
    title = _lazy(u'Unreviewed Changes')

    short_title = _lazy(u'Unreviewed', 'document')
    details_link_text = _lazy(u'All articles requiring review...')
    slug = 'unreviewed'
    column4_label = _lazy(u'Changed')

    def _query_and_params(self, max):
        english_id = ('id' if self.locale == settings.WIKI_DEFAULT_LANGUAGE
                      else 'parent_id')
        return ('SELECT wiki_document.slug, wiki_document.title, '
            'MAX(wiki_revision.created) maxcreated, '
            'GROUP_CONCAT(DISTINCT auth_user.username '
                         "ORDER BY wiki_revision.id SEPARATOR ', '), "
            'dashboards_wikidocumentvisits.visits '
            'FROM wiki_document '
            'INNER JOIN wiki_revision ON '
                        'wiki_document.id=wiki_revision.document_id '
            'INNER JOIN auth_user ON wiki_revision.creator_id=auth_user.id '
            'LEFT JOIN dashboards_wikidocumentvisits ON '
                'wiki_document.' + english_id
                    + '=dashboards_wikidocumentvisits.document_id AND '
                'dashboards_wikidocumentvisits.period=%s '
            'WHERE wiki_revision.reviewed IS NULL '
            'AND (wiki_document.current_revision_id IS NULL OR '
                 'wiki_revision.id>wiki_document.current_revision_id) '
            'AND wiki_document.locale=%s AND NOT wiki_document.is_archived '
            'GROUP BY wiki_document.id '
            + self._order_clause() + self._limit_clause(max),
            (LAST_30_DAYS, self.locale))

    def _order_clause(self):
        return ('ORDER BY maxcreated DESC' if self.mode == MOST_RECENT
                else 'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
                     'wiki_document.title ASC')

    def _format_row(self, (slug, title, changed, users, visits)):
        return dict(title=title,
                    url=reverse('wiki.document_revisions',
                                args=[slug],
                                locale=self.locale),
                    visits=visits,
                    updated=changed,
                    users=users)


class UnhelpfulReadout(Readout):
    title = _lazy(u'Unhelpful Documents')

    short_title = _lazy(u'Unhelpful', 'document')
    details_link_text = _lazy(u'All unhelpful articles...')
    slug = 'unhelpful'
    column3_label = _lazy(u'Total Votes')
    column4_label = _lazy(u'Helpfulness')
    modes = []
    default_mode = None

    # This class is a namespace and doesn't get instantiated.
    key = settings.HELPFULVOTES_UNHELPFUL_KEY
    try:
        hide_readout = redis_client('helpfulvotes').llen(key) == 0
    except RedisError as e:
        log.error('Redis error: %s' % e)
        hide_readout = True

    def rows(self, max=None):
        REDIS_KEY = settings.HELPFULVOTES_UNHELPFUL_KEY
        try:
            redis = redis_client('helpfulvotes')
            length = redis.llen(REDIS_KEY)
            max_get = max or length
            output = redis.lrange(REDIS_KEY, 0, max_get)
        except RedisError as e:
            log.error('Redis error: %s' % e)
            output = []

        return [self._format_row(r) for r in output]

    def _format_row(self, strresult):
        result = strresult.split('::')
        helpfulness = Markup('<span title="%+.1f%%">%.1f%%</span>' %
                             (float(result[3]) * 100, float(result[2]) * 100))
        return dict(title=result[6].decode('utf-8'),
                     url=reverse('wiki.document_revisions',
                                 args=[unicode(result[5], "utf-8")],
                                 locale=self.locale),
                     visits=int(float(result[1])),
                     custom=True,
                     column4_data=helpfulness)


class UnreadyForLocalizationReadout(Readout):
    """Articles which have approved but unready revisions newer than their
    latest ready-for-l10n ones"""
    title = _lazy(u'Changes Not Ready For Localization')
    description = _lazy(u'Articles which have approved revisions newer than '
                         'the latest ready-for-localization one')
    # No short_title; the Contributors dash lacks an Overview readout
    details_link_text = _lazy(u'All articles with changes not ready for '
                               'localization...')
    slug = 'unready'
    column4_label = _lazy(u'Approved')

    def _query_and_params(self, max):
        return ('SELECT wiki_document.slug, wiki_document.title, '
            'MAX(wiki_revision.reviewed) maxreviewed, '
            'visits.visits '
            'FROM wiki_document '
            'INNER JOIN wiki_revision ON '
                        'wiki_document.id=wiki_revision.document_id '
            'LEFT JOIN dashboards_wikidocumentvisits visits ON '
                'wiki_document.id=visits.document_id AND '
                'visits.period=%s '
            'WHERE wiki_document.locale=%s '  # shouldn't be necessary
            'AND NOT wiki_document.is_archived '
            'AND wiki_document.is_localizable '
            'AND (wiki_document.current_revision_id>'
                 'wiki_document.latest_localizable_revision_id OR '
                 'wiki_document.latest_localizable_revision_id IS NULL) '
            # When picking the max(reviewed) date, consider only revisions that
            # are ripe to be marked Ready:
            'AND wiki_revision.is_approved '
            'AND NOT wiki_revision.is_ready_for_localization '
            'AND (wiki_revision.significance>%s OR '
                 'wiki_revision.significance IS NULL) '  # initial revision
            # An optimization: minimize rows before max():
            'AND (wiki_revision.id>'
                 'wiki_document.latest_localizable_revision_id OR '
                 'wiki_document.latest_localizable_revision_id IS NULL) '
            'GROUP BY wiki_document.id '
            + self._order_clause() + self._limit_clause(max),
            (LAST_30_DAYS, settings.WIKI_DEFAULT_LANGUAGE, TYPO_SIGNIFICANCE))

    def _order_clause(self):
        # Put the most recently approved articles first, as those are the most
        # recent to have transitioned onto this dashboard or to change which
        # revision causes them to be on this dashboard.
        return ('ORDER BY maxreviewed DESC' if self.mode == MOST_RECENT
                else 'ORDER BY visits.visits DESC, wiki_document.title ASC')

    def _format_row(self, (slug, title, reviewed, visits)):
        return dict(title=title,
                    url=reverse('wiki.document_revisions',
                                args=[slug],
                                locale=settings.WIKI_DEFAULT_LANGUAGE),
                    visits=visits,
                    updated=reviewed)


class NeedsChangesReadout(Readout):
    """Articles which need change."""
    title = _lazy(u'Need Changes')
    description = _lazy(u'Articles that require changes.')
    # No short_title; the Contributors dash lacks an Overview readout
    details_link_text = _lazy(u'All articles that require changes...')
    slug = 'need-changes'
    column4_label = _lazy(u'Comment')
    modes = [(MOST_VIEWED, _lazy('Most Viewed'))]
    default_mode = MOST_VIEWED

    def _query_and_params(self, max):
        return ('SELECT wiki_document.slug, wiki_document.title, '
            'wiki_document.needs_change_comment, '
            'visits.visits '
            'FROM wiki_document '
            'LEFT JOIN dashboards_wikidocumentvisits visits ON '
                'wiki_document.id=visits.document_id AND '
                'visits.period=%s '
            'WHERE wiki_document.locale=%s '  # shouldn't be necessary
            'AND wiki_document.needs_change '
            'AND NOT wiki_document.is_archived '
            'GROUP BY wiki_document.id '
            + self._order_clause() + self._limit_clause(max),
            (LAST_30_DAYS, settings.WIKI_DEFAULT_LANGUAGE))

    def _order_clause(self):
        # Put the most recently approved articles first, as those are the most
        # recent to have transitioned onto this dashboard or to change which
        # revision causes them to be on this dashboard.
        return ('ORDER BY visits.visits DESC, wiki_document.title ASC')

    def _format_row(self, (slug, title, comment, visits)):
        return dict(title=title,
                    url=reverse('wiki.document_revisions',
                                args=[slug],
                                locale=settings.WIKI_DEFAULT_LANGUAGE),
                    visits=visits,
                    custom=True,
                    column4_data=comment)


# L10n Dashboard tables that have their own whole-page views:
L10N_READOUTS = SortedDict((t.slug, t) for t in
    [MostVisitedTranslationsReadout, NavigationTranslationsReadout,
     TemplateTranslationsReadout, UntranslatedReadout,
     OutOfDateReadout, NeedingUpdatesReadout, UnreviewedReadout])

# Contributors ones:
CONTRIBUTOR_READOUTS = SortedDict((t.slug, t) for t in
    [MostVisitedDefaultLanguageReadout, UnreviewedReadout,
     NeedsChangesReadout, UnreadyForLocalizationReadout, UnhelpfulReadout])

# All:
READOUTS = L10N_READOUTS.copy()
READOUTS.update(CONTRIBUTOR_READOUTS)

GROUP_L10N_READOUTS = SortedDict((t.slug, t) for t in
    [MostVisitedTranslationsReadout, UnreviewedReadout])
# English group locale is the same as l10n dashboard.
GROUP_CONTRIBUTOR_READOUTS = CONTRIBUTOR_READOUTS
