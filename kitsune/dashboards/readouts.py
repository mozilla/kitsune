"""Data aggregators for dashboards

For the purposes of all these numbers, we pretend as if Documents with
is_localizable=False or is_archived=True and Revisions with
is_ready_for_localization=False do not exist.

"""
import logging

from datetime import datetime

from django.conf import settings
from django.db import connections, router
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _, ugettext_lazy as _lazy, pgettext_lazy

import jingo
from jinja2 import Markup
from ordereddict import OrderedDict

from kitsune.dashboards import LAST_30_DAYS, PERIODS
from kitsune.questions.models import QuestionLocale
from kitsune.sumo.helpers import urlparams
from kitsune.sumo.redis_utils import redis_client, RedisError
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.models import Document
from kitsune.wiki.config import (
    MEDIUM_SIGNIFICANCE, MAJOR_SIGNIFICANCE,
    TYPO_SIGNIFICANCE, REDIRECT_HTML,
    HOW_TO_CONTRIBUTE_CATEGORY, ADMINISTRATION_CATEGORY,
    CANNED_RESPONSES_CATEGORY, NAVIGATION_CATEGORY)


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
    '    transdoc.parent_id=engdoc.id '
    '    AND transdoc.locale=%s '
    '    AND EXISTS ('
    '        SELECT * '
    '        FROM wiki_revision transrev_inner '
    '        WHERE transrev_inner.document_id=transdoc.id '
    '        AND NOT (NOT transrev_inner.is_approved '
    '                 AND transrev_inner.reviewed IS NOT NULL) '
    '    ) '
    'LEFT JOIN dashboards_wikidocumentvisits ON engdoc.id='
    '    dashboards_wikidocumentvisits.document_id '
    '    AND dashboards_wikidocumentvisits.period=%s '
    '{extra_joins} '
    'WHERE engdoc.locale=%s '
    '    AND engdoc.is_localizable '
    '    AND NOT engdoc.is_archived '
    '    AND engdoc.latest_localizable_revision_id IS NOT NULL '
    '{extra_where} '
    'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
    '         COALESCE(transdoc.title, engdoc.title) ASC ').format


REVIEW_STATUSES = {
    1: (_lazy(u'Review Needed'), 'wiki.document_revisions', 'review'),
    0: (u'', '', 'ok')}
SIGNIFICANCE_STATUSES = {
    MEDIUM_SIGNIFICANCE: (
        _lazy(u'Update Needed'), 'wiki.edit_document', 'update'),
    MAJOR_SIGNIFICANCE: (
        _lazy(u'Immediate Update Needed'), 'wiki.edit_document',
        'out-of-date')}

# The most significant approved change to the English article between {the
# English revision the current translated revision is based on} and {the latest
# ready-for-localization revision}:
MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE = """
    (SELECT MAX(engrev.significance)
     FROM wiki_revision engrev, wiki_revision transrev
     WHERE engrev.is_approved
     AND transrev.id=transdoc.current_revision_id
     AND engrev.document_id=transdoc.parent_id
     AND engrev.id>transrev.based_on_id
     AND engrev.id<=engdoc.latest_localizable_revision_id)
    """

# Whether there are any unreviewed revs of the translation made since the
# current one:
NEEDS_REVIEW = """
    (SELECT EXISTS
        (SELECT *
         FROM wiki_revision transrev
         WHERE transrev.document_id=transdoc.id
         AND transrev.reviewed IS NULL
         AND (transrev.id>transdoc.current_revision_id OR
              transdoc.current_revision_id IS NULL)
        )
    )
    """

# Whether there are unreviewed revisions of the English doc:
NEEDS_REVIEW_ENG = (
    '(SELECT EXISTS '
    '    (SELECT * '
    '     FROM wiki_revision engrev '
    '     WHERE engrev.document_id=engdoc.id '
    '     AND engrev.reviewed IS NULL '
    '     AND (engrev.id>engdoc.current_revision_id OR '
    '          engdoc.current_revision_id IS NULL)'
    '     )'
    ') ')

# Whether the current revision is not ready for localization
UNREADY_FOR_L10N = (
    '(SELECT EXISTS '
    '    (SELECT * '
    '    FROM wiki_revision rev '
    '    WHERE rev.document_id=engdoc.id '
    '    AND (rev.id>engdoc.latest_localizable_revision_id OR '
    '         engdoc.latest_localizable_revision_id IS NULL) '
    '    AND rev.is_approved '
    '    AND NOT rev.is_ready_for_localization '
    '    AND (rev.significance>%s OR rev.significance IS NULL)'
    '    )'
    ') ')

# Any ready-for-l10n, nontrivial-significance revision of the English doc newer
# than the one our current translation is based on:
ANY_SIGNIFICANT_UPDATES = (
    '(SELECT id FROM wiki_revision engrev '
    ' WHERE engrev.document_id=engdoc.id '
    ' AND engrev.id>curtransrev.based_on_id '
    ' AND engrev.is_ready_for_localization '
    ' AND engrev.significance>=%s) ')

# Filter by products when a product is selected.
PRODUCT_FILTER = (
    'INNER JOIN wiki_document_products docprod ON '
    '    docprod.document_id=engdoc.id '
    '    AND docprod.product_id=%s ')


def _cursor():
    """Return a DB cursor for reading."""
    return connections[router.db_for_read(Document)].cursor()


def _format_row_with_out_of_dateness(readout_locale, eng_slug, eng_title, slug,
                                     title, visits, significance,
                                     needs_review):
    """Format a row for a readout that has the traffic-light-style
    categorization of how seriously out of date a translation is."""
    if slug:  # A translation exists but may not be approved.
        locale = readout_locale
        if needs_review:
            status, view_name, status_class = REVIEW_STATUSES[needs_review]
        else:
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


def kb_overview_rows(mode=None, max=None, locale=None, product=None, category=None):
    """Return the iterable of dicts needed to draw the new KB dashboard overview"""

    if mode is None:
        mode = LAST_30_DAYS

    docs = Document.objects.filter(locale=settings.WIKI_DEFAULT_LANGUAGE,
                                   is_archived=False,
                                   is_template=False)

    docs = docs.exclude(html__startswith=REDIRECT_HTML)

    select = OrderedDict([
        ('num_visits', 'SELECT `wdv`.`visits` '
                       'FROM `dashboards_wikidocumentvisits` as `wdv` '
                       'WHERE `wdv`.`period`=%s '
                       'AND `wdv`.`document_id`=`wiki_document`.`id`'),
    ])

    docs = docs.extra(select=select,
                      select_params=(mode,))

    if product:
        docs = docs.filter(products__in=[product])

    if category:
        docs = docs.filter(category__in=[category])

    docs = docs.order_by('-num_visits', 'title')

    if max:
        docs = docs[:max]

    rows = []

    if docs.count():
        max_visits = docs[0].num_visits

    for d in docs:
        data = {
            'url': reverse('wiki.document', args=[d.slug],
                           locale=settings.WIKI_DEFAULT_LANGUAGE),
            'trans_url': reverse('wiki.show_translations', args=[d.slug],
                                 locale=settings.WIKI_DEFAULT_LANGUAGE),
            'title': d.title,
            'num_visits': d.num_visits,
            'ready_for_l10n': d.revisions.filter(is_approved=True,
                                                 is_ready_for_localization=True).exists()
        }

        if d.current_revision:
            data['expiry_date'] = d.current_revision.expires

        if d.num_visits:
            data['visits_ratio'] = float(d.num_visits) / max_visits

        if 'expiry_date' in data and data['expiry_date']:
            data['stale'] = data['expiry_date'] < datetime.now()

        # Check L10N status
        if d.current_revision:
            unapproved_revs = d.revisions.filter(
                reviewed=None, id__gt=d.current_revision.id)[:1]
        else:
            unapproved_revs = d.revisions.all()

        if unapproved_revs.count():
            data['revision_comment'] = unapproved_revs[0].comment
        else:
            data['latest_revision'] = True

        # Get the translated doc
        if locale != settings.WIKI_DEFAULT_LANGUAGE:
            transdoc = d.translations.filter(
                locale=locale,
                is_archived=False).first()

            if transdoc:
                data['needs_update'] = transdoc.is_outdated()
        else:  # For en-US we show the needs_changes comment.
            data['needs_update'] = d.needs_change
            data['needs_update_comment'] = d.needs_change_comment

        rows.append(data)

    return rows


def l10n_overview_rows(locale, product=None):
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

    total = Document.objects.filter(
        locale=settings.WIKI_DEFAULT_LANGUAGE,
        is_archived=False,
        current_revision__isnull=False,
        is_localizable=True,
        latest_localizable_revision__isnull=False)
    total = total.exclude(
        html__startswith=REDIRECT_HTML)

    if product:
        total = total.filter(products=product)
        has_forum = product.questions_locales.filter(locale=locale).exists()

    ignore_categories = [str(ADMINISTRATION_CATEGORY),
                         str(NAVIGATION_CATEGORY),
                         str(HOW_TO_CONTRIBUTE_CATEGORY)]

    if product and not has_forum:
        ignore_categories.append(str(CANNED_RESPONSES_CATEGORY))

    total = total.exclude(category__in=ignore_categories)

    total_docs = total.filter(is_template=False).count()
    total_templates = total.filter(is_template=True).count()

    if product:
        extra_joins = PRODUCT_FILTER
        prod_param = (product.id,)
    else:
        extra_joins = ''
        prod_param = tuple()

    # Translations whose based_on revision has no >10-significance, ready-for-
    # l10n revisions after it. It *might* be possible to do this with the ORM
    # by passing wheres and tables to extra():
    up_to_date_translation_count = (
        'SELECT COUNT(*) FROM wiki_document transdoc '
        'INNER JOIN wiki_document engdoc ON transdoc.parent_id=engdoc.id '
        'INNER JOIN wiki_revision curtransrev '
        '    ON transdoc.current_revision_id=curtransrev.id ' +
        extra_joins +
        'WHERE transdoc.locale=%s '
        '    AND engdoc.category NOT IN '
        '        (' + ','.join(ignore_categories) + ')'
        '    AND transdoc.is_template=%s '
        '    AND NOT transdoc.is_archived '
        '    AND engdoc.latest_localizable_revision_id IS NOT NULL '
        '    AND engdoc.is_localizable '
        '    AND engdoc.html NOT LIKE "<p>REDIRECT <a%%" '
        '    AND NOT EXISTS ' +
        ANY_SIGNIFICANT_UPDATES)
    translated_docs = single_result(
        up_to_date_translation_count,
        prod_param + (locale, False, MEDIUM_SIGNIFICANCE))
    translated_templates = single_result(
        up_to_date_translation_count,
        prod_param + (locale, True, MEDIUM_SIGNIFICANCE))

    # Of the top N most visited English articles, how many have up-to-date
    # translations into German?
    #
    # TODO: Be very suspicious of this query. It selects from a subquery (known
    # to MySQL's EXPLAIN as a "derived" table), and MySQL always materializes
    # such subqueries and never builds indexes on them. However, it seems to be
    # fast in practice.
    top_n_query = (
        'SELECT SUM(istranslated) FROM '
        '    (SELECT transdoc.current_revision_id IS NOT NULL '
        # And there have been no significant updates since the current
        # translation:
        '        AND NOT EXISTS ' + ANY_SIGNIFICANT_UPDATES +
        '        AS istranslated ' +
        most_visited_translation_from(
            extra_joins='LEFT JOIN wiki_revision curtransrev '
                        'ON transdoc.current_revision_id=curtransrev.id ' +
                        extra_joins,
            extra_where='AND engdoc.category NOT IN (' +
                        ','.join(ignore_categories) + ') ' +
                        'AND NOT engdoc.is_template ' +
                        'AND engdoc.html NOT LIKE "<p>REDIRECT <a%%" ') +
        'LIMIT %s) t1 ')

    top_20_translated = int(single_result(  # Driver returns a Decimal.
        top_n_query,
        (MEDIUM_SIGNIFICANCE, locale, LAST_30_DAYS) + prod_param +
        (settings.WIKI_DEFAULT_LANGUAGE, 20)) or 0)  # SUM can return NULL.
    top_50_translated = int(single_result(  # Driver returns a Decimal.
        top_n_query,
        (MEDIUM_SIGNIFICANCE, locale, LAST_30_DAYS) + prod_param +
        (settings.WIKI_DEFAULT_LANGUAGE, 50)) or 0)  # SUM can return NULL.
    top_100_translated = int(single_result(  # Driver returns a Decimal.
        top_n_query,
        (MEDIUM_SIGNIFICANCE, locale, LAST_30_DAYS) + prod_param +
        (settings.WIKI_DEFAULT_LANGUAGE, 100)) or 0)  # SUM can return NULL.

    return {
        'top-20': {
            'title': _('Top 20 Articles'),
            'numerator': top_20_translated,
            'denominator': 20 if total_docs > 20 else total_docs,
            'percent': percent_or_100(
                top_20_translated, 20 if total_docs > 20 else total_docs),
            'description': _('These are the top 20 most visited articles '
                             'in the last 30 days, which account for over '
                             '50% of the traffic to the Knowledge Base.'),
        },
        'top-50': {
            'title': _('Top 50 Articles'),
            'numerator': top_50_translated,
            'denominator': 50 if total_docs > 50 else total_docs,
            'percent': percent_or_100(
                top_50_translated, 50 if total_docs > 50 else total_docs),
            'description': _('These are the top 50 most visited articles '
                             'in the last 30 days.'),
        },
        'top-100': {
            'title': _('Top 100 Articles'),
            'numerator': top_100_translated,
            'denominator': 100 if total_docs > 100 else total_docs,
            'percent': percent_or_100(
                top_100_translated, 100 if total_docs > 100 else total_docs),
            'description': _('These are the top 100 most visited articles '
                             'in the last 30 days, which account for over '
                             '99% of the traffic to the Knowledge Base.'),
        },
        'templates': {
            'title': _('Templates'),
            'url': '#' + TemplateTranslationsReadout.slug,
            'numerator': translated_templates,
            'denominator': total_templates,
            'percent': percent_or_100(translated_templates, total_templates),
            'description': _('Templates are a way of reusing pieces of '
                             'content across KB articles. You can create and '
                             'update a set of instructions in one place, and '
                             'then refer to it in other pages.'),
        },
        'all': {
            'title': _('All Knowledge Base Articles'),
            'numerator': translated_docs,
            'denominator': total_docs,
            'percent': percent_or_100(translated_docs, total_docs),
            'description': _('This is the number of all Knowledge Base '
                             'articles that are ready to be localized.'),
        }
    }


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

    def __init__(self, request, locale=None, mode=None, product=None):
        """Take request so the template can use contextual macros that need it.

        Renders the data for the locale specified by the request, but you can
        override it by passing another in `locale`.

        """
        self.request = request
        self.locale = locale or request.LANGUAGE_CODE
        self.mode = mode if mode is not None else self.default_mode
        # self.mode is allowed to be invalid.
        self.product = product

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

    def render(self, max_rows=None, rows=None):
        """Return HTML table rows, optionally limiting to a number of rows."""
        # Fetch the rows if they aren't passed.
        if not rows:
            rows = self.rows(max_rows)

        # Compute percents for bar widths:
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

    @classmethod
    def should_show_to(cls, request):
        """Whether this readout should be shown on the request."""
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

    def get_absolute_url(self, locale, product=None):
        if self.slug in L10N_READOUTS:
            url = reverse('dashboards.localization_detail',
                          kwargs={'readout_slug': self.slug}, locale=locale)
        elif self.slug in CONTRIBUTOR_READOUTS:
            url = reverse('dashboards.contributors_detail',
                          kwargs={'readout_slug': self.slug}, locale=locale)
        else:
            raise KeyError('This Readout was not found: %s' % self.slug)

        if product:
            return urlparams(url, product=product.slug)

        return url


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

        # Filter by product if specified.
        if self.product:
            extra_joins = PRODUCT_FILTER
            params = (period, self.product.id, self.locale)
        else:
            extra_joins = ''
            params = (period, self.locale)

        # Review Needed: link to /history.
        query = (
            'SELECT engdoc.slug, engdoc.title, '
            'dashboards_wikidocumentvisits.visits, '
            'count(engrev.document_id) '
            'FROM wiki_document engdoc '
            'LEFT JOIN dashboards_wikidocumentvisits ON '
            '    engdoc.id=dashboards_wikidocumentvisits.document_id '
            '    AND dashboards_wikidocumentvisits.period=%s '
            'LEFT JOIN wiki_revision engrev ON '
            '    engrev.document_id=engdoc.id '
            '    AND engrev.reviewed IS NULL '
            '    AND engrev.id>engdoc.current_revision_id ' +
            extra_joins +
            'WHERE engdoc.locale=%s AND '
            'NOT engdoc.is_archived AND '
            'NOT engdoc.category IN (' + (
                str(ADMINISTRATION_CATEGORY) + ', ' +
                str(NAVIGATION_CATEGORY) + ', ' +
                str(CANNED_RESPONSES_CATEGORY) + ', ' +
                str(HOW_TO_CONTRIBUTE_CATEGORY)) +
            ') AND '
            'NOT engdoc.is_template AND '
            'engdoc.html NOT LIKE "<p>REDIRECT <a%%" '
            'GROUP BY engdoc.id '
            'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
            '    engdoc.title ASC' + self._limit_clause(max))

        return query, params

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


class CategoryReadout(Readout):
    """Abstract class representing a readout ordered by visits and intended
    to be filtered by category."""
    column3_label = _lazy(u'Visits')
    modes = []
    default_mode = None
    where_clause = ''

    def _query_and_params(self, max):
        # Filter by product if specified.
        if self.product:
            extra_joins = PRODUCT_FILTER
            params = (TYPO_SIGNIFICANCE, LAST_30_DAYS, self.product.id,
                      self.locale)
        else:
            extra_joins = ''
            params = (TYPO_SIGNIFICANCE, LAST_30_DAYS, self.locale)

        # Review Needed: link to /history.
        query = (
            'SELECT engdoc.slug, engdoc.title, '
            '   dashboards_wikidocumentvisits.visits, '
            '   engdoc.needs_change, ' + (
                NEEDS_REVIEW_ENG + ', ' +
                UNREADY_FOR_L10N) +
            'FROM wiki_document engdoc '
            'LEFT JOIN dashboards_wikidocumentvisits ON '
            '   engdoc.id=dashboards_wikidocumentvisits.document_id '
            '   AND dashboards_wikidocumentvisits.period=%s ' +
            extra_joins +
            'WHERE engdoc.locale=%s AND '
            '   NOT engdoc.is_archived ' + (
                self.where_clause) +
            'GROUP BY engdoc.id '
            'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
            '    engdoc.title ASC' + self._limit_clause(max))

        return query, params

    def _format_row(self, (slug, title, visits, needs_changes, needs_review,
                           unready_for_l10n)):
        if needs_review:
            status, view_name, dummy = REVIEW_STATUSES[needs_review]
        elif needs_changes:
            status = _lazy(u'Changes Needed')
            view_name = 'wiki.document_revisions'
        elif unready_for_l10n:
            status = _lazy(u'Changes Not Ready For Localization')
            view_name = 'wiki.document_revisions'
        else:
            status, view_name, dummy = REVIEW_STATUSES[0]

        return dict(title=title,
                    url=reverse('wiki.document', args=[slug],
                                locale=self.locale),
                    visits=visits,
                    status=status,
                    status_url=reverse(view_name, args=[slug],
                                       locale=self.locale)
                    if view_name else '')


class TemplateReadout(CategoryReadout):
    title = _lazy(u'Templates')
    slug = 'templates'
    details_link_text = _lazy(u'All templates...')
    where_clause = 'AND engdoc.is_template '


class HowToContributeReadout(CategoryReadout):
    title = _lazy(u'How To Contribute')
    slug = 'how-to-contribute'
    details_link_text = _lazy(u'All How To Contribute articles...')
    where_clause = 'AND engdoc.category=%s ' % HOW_TO_CONTRIBUTE_CATEGORY


class AdministrationReadout(CategoryReadout):
    title = _lazy(u'Administration')
    slug = 'administration'
    details_link_text = _lazy(u'All Administration articles...')
    where_clause = 'AND engdoc.category=%s ' % ADMINISTRATION_CATEGORY


class MostVisitedTranslationsReadout(MostVisitedDefaultLanguageReadout):
    """Most-Visited readout for non-default languages

    Adds a few subqueries to determine the status of translations.

    Shows the articles that are most visited in English, even if there are no
    translations of those articles yet. This draws attention to articles that
    we should drop everything to translate.

    """
    short_title = _lazy(u'Most Visited')
    slug = 'most-visited-translations'
    details_link_text = _lazy(u'All translations...')

    def _query_and_params(self, max):
        if self.mode in [m[0] for m in self.modes]:
            period = self.mode
        else:
            period = self.default_mode

        ignore_categories = [str(ADMINISTRATION_CATEGORY),
                             str(NAVIGATION_CATEGORY),
                             str(HOW_TO_CONTRIBUTE_CATEGORY)]

        # Filter by product if specified.
        if self.product:
            extra_joins = PRODUCT_FILTER
            params = (self.locale, period, self.product.id,
                      settings.WIKI_DEFAULT_LANGUAGE)

            has_forum = self.product.questions_locales.filter(locale=self.locale).exists()
        else:
            extra_joins = ''
            params = (self.locale, period, settings.WIKI_DEFAULT_LANGUAGE)

        if self.product and not has_forum:
            ignore_categories.append(str(CANNED_RESPONSES_CATEGORY))

        extra_where = ('AND NOT engdoc.category IN (' +
                       ', '.join(ignore_categories) +
                       ') ')

        # Immediate Update Needed or Update Needed: link to /edit.
        # Review Needed: link to /history.
        # These match the behavior of the corresponding readouts.
        return (
            'SELECT engdoc.slug, engdoc.title, transdoc.slug, '
            'transdoc.title, dashboards_wikidocumentvisits.visits, ' +
            MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE + ', ' +
            NEEDS_REVIEW +
            most_visited_translation_from(extra_joins=extra_joins,
                                          extra_where=extra_where) +
            self._limit_clause(max), params)

    def _format_row(self, columns):
        return _format_row_with_out_of_dateness(self.locale, *columns)

    def render(self, max_rows=None, rows=None):
        """Override parent render to add some filtering."""
        # Compute percents for bar widths:
        rows = self.rows()

        if max_rows is not None:
            # If we specify max_rows, we are on the l10n dashboard
            # overview page and want to filter out all up to date docs.
            # NOTE: This is a HACK! But I would rather filter here
            # than figure out the SQL to do this. And I don't know
            # any other way to filter in one view and not the other.
            # BTW, OK means the translation is up to date. Those are
            # the ones we are skipping.
            rows = filter(lambda x: x['status_class'] != 'ok', rows)
            rows = rows[:max_rows]

        return super(MostVisitedTranslationsReadout, self).render(rows=rows)


class TemplateTranslationsReadout(Readout):
    """Readout for templates in non-default languages

    Shows the templates even if there are no translations of them yet.
    This draws attention to templates that we should drop everything to
    translate.

    """
    title = _lazy(u'Templates')
    short_title = _lazy(u'Templates')
    slug = 'template-translations'
    details_link_text = _lazy(u'All templates...')
    column3_label = ''
    modes = []
    default_mode = None

    def _query_and_params(self, max):
        # Filter by product if specified.
        if self.product:
            extra_joins = PRODUCT_FILTER
            params = (self.locale, self.product.id,
                      settings.WIKI_DEFAULT_LANGUAGE)
        else:
            extra_joins = ''
            params = (self.locale, settings.WIKI_DEFAULT_LANGUAGE)

        query = (
            'SELECT engdoc.slug, engdoc.title, transdoc.slug, '
            'transdoc.title, ' +
            MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE + ', ' +
            NEEDS_REVIEW +

            'FROM wiki_document engdoc '
            'LEFT JOIN wiki_document transdoc ON '
            '    transdoc.parent_id=engdoc.id '
            '    AND transdoc.locale=%s ' +
            extra_joins +
            'WHERE engdoc.locale=%s '
            '    AND engdoc.is_localizable '
            '    AND NOT engdoc.is_archived '
            '    AND engdoc.latest_localizable_revision_id IS NOT NULL '
            '    AND engdoc.is_template ')

        return query, params

    def _format_row(self, (eng_slug, eng_title, slug, title, significance,
                           needs_review)):
        return _format_row_with_out_of_dateness(
            self.locale, eng_slug, eng_title, slug, title, None, significance,
            needs_review)

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


class UnreviewedReadout(Readout):
    # L10n: Not just changes to translations but also unreviewed changes to
    # docs in this locale that are not translations
    title = _lazy(u'Unreviewed Changes')

    short_title = pgettext_lazy('document', u'Unreviewed')
    details_link_text = _lazy(u'All articles requiring review...')
    slug = 'unreviewed'
    column4_label = _lazy(u'Changed')

    def _query_and_params(self, max):
        english_id = ('id' if self.locale == settings.WIKI_DEFAULT_LANGUAGE
                      else 'parent_id')

        # Filter by product if specified.
        if self.product:
            extra_joins = (
                'INNER JOIN wiki_document_products docprod ON '
                '    docprod.document_id=wiki_document.' + english_id + ' '
                '    AND docprod.product_id=%s ')
            params = (LAST_30_DAYS, self.product.id, self.locale)
        else:
            extra_joins = ''
            params = (LAST_30_DAYS, self.locale)

        query = (
            'SELECT wiki_document.slug, wiki_document.title, '
            'MAX(wiki_revision.created) maxcreated, '
            'GROUP_CONCAT(DISTINCT auth_user.username '
            "             ORDER BY wiki_revision.id SEPARATOR ', '), "
            'dashboards_wikidocumentvisits.visits '
            'FROM wiki_document '
            'INNER JOIN wiki_revision ON '
            '            wiki_document.id=wiki_revision.document_id '
            'INNER JOIN auth_user ON wiki_revision.creator_id=auth_user.id '
            'LEFT JOIN dashboards_wikidocumentvisits ON '
            '    wiki_document.' + english_id +
            '        =dashboards_wikidocumentvisits.document_id AND '
            '    dashboards_wikidocumentvisits.period=%s ' +
            extra_joins +
            'WHERE wiki_revision.reviewed IS NULL '
            'AND (wiki_document.current_revision_id IS NULL OR '
            '     wiki_revision.id>wiki_document.current_revision_id) '
            'AND wiki_document.locale=%s AND NOT wiki_document.is_archived '
            'GROUP BY wiki_document.id ' +
            self._order_clause() + self._limit_clause(max))

        return query, params

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

    short_title = pgettext_lazy('document', u'Unhelpful')
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

        data = []
        for r in output:
            row = self._format_row(r)
            if row:
                data.append(row)

        return data

    def _format_row(self, strresult):
        result = strresult.split('::')

        # Filter by product
        if self.product:
            doc = Document.objects.filter(products__in=[self.product],
                                          slug=result[5])
            if not doc.count():
                return None

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
                        u'the latest ready-for-localization one')
    # No short_title; the Contributors dash lacks an Overview readout
    details_link_text = _lazy(u'All articles with changes not ready for '
                              u'localization...')
    slug = 'unready'
    column4_label = _lazy(u'Approved')

    def _query_and_params(self, max):
        # Filter by product if specified.
        if self.product:
            extra_joins = PRODUCT_FILTER
            params = (LAST_30_DAYS, self.product.id,
                      settings.WIKI_DEFAULT_LANGUAGE, TYPO_SIGNIFICANCE)
        else:
            extra_joins = ''
            params = (LAST_30_DAYS, settings.WIKI_DEFAULT_LANGUAGE,
                      TYPO_SIGNIFICANCE)

        query = (
            'SELECT engdoc.slug, engdoc.title, '
            'MAX(wiki_revision.reviewed) maxreviewed, '
            'visits.visits '
            'FROM wiki_document engdoc '
            'INNER JOIN wiki_revision ON '
            '            engdoc.id=wiki_revision.document_id '
            'LEFT JOIN dashboards_wikidocumentvisits visits ON '
            '    engdoc.id=visits.document_id AND '
            '    visits.period=%s ' +
            extra_joins +
            'WHERE engdoc.locale=%s '  # shouldn't be necessary
            'AND NOT engdoc.is_archived '
            'AND engdoc.is_localizable '
            'AND (engdoc.current_revision_id>'
            '     engdoc.latest_localizable_revision_id OR '
            '     engdoc.latest_localizable_revision_id IS NULL) '
            # When picking the max(reviewed) date, consider only revisions that
            # are ripe to be marked Ready:
            'AND wiki_revision.is_approved '
            'AND NOT wiki_revision.is_ready_for_localization '
            'AND (wiki_revision.significance>%s OR '
            '     wiki_revision.significance IS NULL) '  # initial revision
            # An optimization: minimize rows before max():
            'AND (wiki_revision.id>'
            '     engdoc.latest_localizable_revision_id OR '
            '     engdoc.latest_localizable_revision_id IS NULL) '
            'GROUP BY engdoc.id ' +
            self._order_clause() + self._limit_clause(max))

        return query, params

    def _order_clause(self):
        # Put the most recently approved articles first, as those are the most
        # recent to have transitioned onto this dashboard or to change which
        # revision causes them to be on this dashboard.
        return ('ORDER BY maxreviewed DESC' if self.mode == MOST_RECENT
                else 'ORDER BY visits.visits DESC, engdoc.title ASC')

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
        # Filter by product if specified.
        if self.product:
            extra_joins = PRODUCT_FILTER
            params = (LAST_30_DAYS, self.product.id,
                      settings.WIKI_DEFAULT_LANGUAGE)
        else:
            extra_joins = ''
            params = (LAST_30_DAYS, settings.WIKI_DEFAULT_LANGUAGE)

        query = (
            'SELECT engdoc.slug, engdoc.title, '
            '   engdoc.needs_change_comment, '
            '   visits.visits '
            'FROM wiki_document engdoc '
            'LEFT JOIN dashboards_wikidocumentvisits visits ON '
            '    engdoc.id=visits.document_id AND '
            '    visits.period=%s ' +
            extra_joins +
            'WHERE engdoc.locale=%s '  # shouldn't be necessary
            'AND engdoc.needs_change '
            'AND NOT engdoc.is_archived '
            'GROUP BY engdoc.id ' +
            self._order_clause() + self._limit_clause(max))

        return query, params

    def _order_clause(self):
        # Put the most recently approved articles first, as those are the most
        # recent to have transitioned onto this dashboard or to change which
        # revision causes them to be on this dashboard.
        return ('ORDER BY visits.visits DESC, engdoc.title ASC')

    def _format_row(self, (slug, title, comment, visits)):
        return dict(title=title,
                    url=reverse('wiki.document_revisions',
                                args=[slug],
                                locale=settings.WIKI_DEFAULT_LANGUAGE),
                    visits=visits,
                    custom=True,
                    column4_data=comment)


class CannedResponsesReadout(Readout):
    title = _lazy(u'Canned Responses')
    description = _lazy(u'Localization status of all canned responses')
    slug = 'canned-responses'
    details_link_text = _lazy(u'All canned responses articles...')

    @classmethod
    def should_show_to(cls, request):
        return request.LANGUAGE_CODE in QuestionLocale.objects.locales_list()

    def _query_and_params(self, max):

        if self.product:
            params = [self.locale, LAST_30_DAYS, self.product.id,
                      CANNED_RESPONSES_CATEGORY,
                      settings.WIKI_DEFAULT_LANGUAGE]
            extra_joins = PRODUCT_FILTER
        else:
            params = [self.locale, LAST_30_DAYS, CANNED_RESPONSES_CATEGORY,
                      settings.WIKI_DEFAULT_LANGUAGE]
            extra_joins = ''

        query = (
            'SELECT engdoc.slug, engdoc.title, '
            '    transdoc.slug, transdoc.title, '
            '    engvisits.visits, ' +
            MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE + ', ' +
            NEEDS_REVIEW +
            'FROM wiki_document engdoc '
            'LEFT JOIN wiki_document transdoc ON '
            '    transdoc.parent_id=engdoc.id '
            '    AND transdoc.locale=%s '
            'LEFT JOIN dashboards_wikidocumentvisits engvisits ON '
            '    engdoc.id=engvisits.document_id '
            '    AND engvisits.period=%s ' +
            extra_joins +
            'WHERE engdoc.category = %s '
            '    AND engdoc.locale = %s '
            '    AND NOT engdoc.is_archived '
            'ORDER BY engvisits.visits DESC ' +
            self._limit_clause(max)
        )

        return query, params

    def _format_row(self, row):
        return _format_row_with_out_of_dateness(self.locale, *row)


# L10n Dashboard tables that have their own whole-page views:
L10N_READOUTS = SortedDict(
    (t.slug, t) for t in
    [MostVisitedTranslationsReadout, TemplateTranslationsReadout,
     UnreviewedReadout])

# Contributors ones:
CONTRIBUTOR_READOUTS = SortedDict(
    (t.slug, t) for t in
    [MostVisitedDefaultLanguageReadout, TemplateReadout,
     HowToContributeReadout, AdministrationReadout, UnreviewedReadout,
     NeedsChangesReadout, UnreadyForLocalizationReadout, UnhelpfulReadout])

# All:
READOUTS = L10N_READOUTS.copy()
READOUTS.update(CONTRIBUTOR_READOUTS)

GROUP_L10N_READOUTS = SortedDict(
    (t.slug, t) for t in
    [MostVisitedTranslationsReadout, UnreviewedReadout])
# English group locale is the same as l10n dashboard.
GROUP_CONTRIBUTOR_READOUTS = CONTRIBUTOR_READOUTS
