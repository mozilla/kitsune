"""Data aggregators for dashboards

For the purposes of all these numbers, we pretend as if Documents with
is_localizable=False or is_archived=True and Revisions with
is_ready_for_localization=False do not exist.

"""

import logging
from collections import OrderedDict
from datetime import datetime

from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Case, Count, Exists, F, Max, OuterRef, Q, Subquery, When
from django.db.models.functions import Coalesce
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import pgettext_lazy
from markupsafe import Markup

from kitsune.dashboards import LAST_30_DAYS, PERIODS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.questions.models import AAQConfig
from kitsune.sumo.redis_utils import RedisError, redis_client
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.config import (
    ADMINISTRATION_CATEGORY,
    CANNED_RESPONSES_CATEGORY,
    HOW_TO_CONTRIBUTE_CATEGORY,
    MAJOR_SIGNIFICANCE,
    MEDIUM_SIGNIFICANCE,
    NAVIGATION_CATEGORY,
    REDIRECT_HTML,
    TYPO_SIGNIFICANCE,
)
from kitsune.wiki.models import Document, Revision

log = logging.getLogger("k.dashboards.readouts")


MOST_VIEWED = 1
MOST_RECENT = 2
REVIEW_STATUSES = {
    # L10n: This is a KB article localization status. It may be displayed on
    # https://support.mozilla.org/localization or
    # https://support.mozilla.org/localization/most-visited-translations (for non-en-US locales).
    # Note: the article may already be translated; the status is displayed if there is at least one unreviewed revision.
    1: (_lazy("Review Needed"), "wiki.document_revisions", "review"),
    # L10n: This is a KB article localization status. It may be displayed on
    # https://support.mozilla.org/localization or
    # https://support.mozilla.org/localization/most-visited-translations (for non-en-US locales).
    0: (_lazy("Up to Date"), "", "ok"),
}
SIGNIFICANCE_STATUSES = {
    # L10n: This is a KB article localization status. It may be displayed on
    # https://support.mozilla.org/localization or
    # https://support.mozilla.org/localization/most-visited-translations (for non-en-US locales).
    MEDIUM_SIGNIFICANCE: (_lazy("Update Needed"), "wiki.edit_document", "update"),
    # L10n: This is a KB article localization status. It may be displayed on
    # https://support.mozilla.org/localization or
    # https://support.mozilla.org/localization/most-visited-translations (for non-en-US locales).
    MAJOR_SIGNIFICANCE: (_lazy("Immediate Update Needed"), "wiki.edit_document", "out-of-date"),
}
MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE_SUBQUERY = Subquery(
    Revision.objects.filter(
        document=OuterRef("pk"),
        is_approved=True,
    )
    .filter(
        id__gt=OuterRef("transdoc_current_revision_based_on_id"),
        id__lte=F("document__latest_localizable_revision__id"),
    )
    .order_by()
    .values("document")
    .annotate(max_significance=Max("significance"))
    .values("max_significance")
)


def get_visits_subquery(document=OuterRef("pk"), period=LAST_30_DAYS):
    return Subquery(
        WikiDocumentVisits.objects.filter(document=document, period=period).values("visits")
    )


def visible_translation_exists(user, locale):
    """
    Returns a combinable queryset expression for Document queries that only
    includes documents that have a translation for the given locale that is
    visible to the given user.
    """
    return Exists(
        Document.objects.visible(
            user,
            locale=locale,
            parent=OuterRef("pk"),
        )
    )


def no_translation_exists(locale):
    """
    Returns a combinable queryset expression for Document queries that only
    includes documents that do not have a translation for the given locale.
    """
    return ~Q(translations__locale=locale)


def row_to_dict_with_out_of_dateness(
    readout_locale, eng_slug, eng_title, slug, title, visits, significance, needs_review
):
    """Format a row for a readout that has the traffic-light-style
    categorization of how seriously out of date a translation is."""
    if slug:  # A translation exists but may not be approved.
        locale = readout_locale
        if needs_review:
            status, view_name, status_class = REVIEW_STATUSES[needs_review]
        else:
            status, view_name, status_class = SIGNIFICANCE_STATUSES.get(
                significance, REVIEW_STATUSES[needs_review]
            )
        status_url = reverse(view_name, args=[slug], locale=locale) if view_name else ""
    else:
        slug = eng_slug
        title = eng_title
        locale = settings.WIKI_DEFAULT_LANGUAGE
        # L10n: This is a KB article localization status. It may be displayed on
        # https://support.mozilla.org/localization or
        # https://support.mozilla.org/localization/most-visited-translations (for non-en-US locales).
        status = _("Translation Needed")
        # When calling the translate view, specify locale to translate to:
        status_url = reverse("wiki.translate", args=[slug], locale=readout_locale)
        status_class = "untranslated"

    return {
        "title": title,
        "url": reverse("wiki.document", args=[slug], locale=locale),
        "visits": visits,
        "status": status,
        "status_class": status_class,
        "status_url": status_url,
    }


def kb_overview_rows(user=None, mode=None, max=None, locale=None, product=None, category=None):
    """Return the iterable of dicts needed to draw the new KB dashboard overview"""

    if mode is None:
        mode = LAST_30_DAYS

    docs = (
        Document.objects.visible(user, locale=settings.WIKI_DEFAULT_LANGUAGE, is_archived=False)
        .exclude(html__startswith=REDIRECT_HTML)
        .select_related("current_revision")
    )

    if product:
        docs = docs.filter(products__in=[product])

    if category:
        docs = docs.filter(category__in=[category])

    docs = docs.annotate(
        num_visits=get_visits_subquery(period=mode),
        ready_for_l10n=Case(
            When(
                Q(latest_localizable_revision__isnull=False)
                & ~Exists(
                    Revision.objects.filter(
                        document=OuterRef("pk"),
                        is_approved=True,
                        is_ready_for_localization=False,
                        significance__gt=TYPO_SIGNIFICANCE,
                        id__gt=F("document__latest_localizable_revision__id"),
                    )
                ),
                then=True,
            ),
            default=False,
        ),
        unapproved_revision_comment=Subquery(
            Revision.objects.filter(
                document=OuterRef("pk"),
                reviewed=None,
            )
            .filter(
                Q(document__current_revision__isnull=True)
                | Q(id__gt=F("document__current_revision__id"))
            )
            .order_by("created")[:1]
            .values("comment")
        ),
    )

    if locale and (locale != settings.WIKI_DEFAULT_LANGUAGE):
        transdoc_subquery = Document.objects.filter(
            locale=locale,
            is_archived=False,
            parent=OuterRef("pk"),
            current_revision__isnull=False,
        )
        docs = docs.annotate(
            transdoc_exists=Exists(transdoc_subquery),
            transdoc_current_revision_based_on_id=Subquery(
                transdoc_subquery.values("current_revision__based_on__id")
            ),
        ).annotate(
            transdoc_is_outdated=Exists(
                Revision.objects.filter(
                    document=OuterRef("pk"),
                    is_approved=True,
                    is_ready_for_localization=True,
                    significance__gte=MEDIUM_SIGNIFICANCE,
                    id__gt=OuterRef("transdoc_current_revision_based_on_id"),
                )
            ),
        )

    docs = docs.order_by(F("num_visits").desc(nulls_last=True), "title")

    if max:
        docs = docs[:max]

    rows = []

    max_visits = docs[0].num_visits if docs.count() else None

    for d in docs:
        data = {
            "url": reverse("wiki.document", args=[d.slug], locale=settings.WIKI_DEFAULT_LANGUAGE),
            "trans_url": reverse(
                "wiki.show_translations", args=[d.slug], locale=settings.WIKI_DEFAULT_LANGUAGE
            ),
            "title": d.title,
            "num_visits": d.num_visits,
            "ready_for_l10n": d.ready_for_l10n,
        }

        if d.current_revision:
            data["expiry_date"] = d.current_revision.expires

        if d.num_visits and max_visits:
            data["visits_ratio"] = float(d.num_visits) / max_visits

        if data.get("expiry_date"):
            data["stale"] = data["expiry_date"] < datetime.now()

        if d.unapproved_revision_comment is None:
            data["latest_revision"] = True
        else:
            data["revision_comment"] = d.unapproved_revision_comment

        # Get the translated doc
        if locale and (locale != settings.WIKI_DEFAULT_LANGUAGE):
            if d.transdoc_exists:
                data["needs_update"] = d.transdoc_is_outdated
        else:  # For en-US we show the needs_changes comment.
            data["needs_update"] = d.needs_change
            data["needs_update_comment"] = d.needs_change_comment

        rows.append(data)

    return rows


def l10n_overview_rows(locale, product=None, user=None):
    """Return the iterable of dicts needed to draw the Overview table."""
    # The Overview table is a special case: it has only a static number of
    # rows, so it has no expanded, all-rows view, and thus needs no slug, no
    # "max" kwarg on rows(), etc. It doesn't fit the Readout signature, so we
    # don't shoehorn it in.

    def percent_or_100(num, denom):
        return round(num / float(denom) * 100) if denom else 100

    ignore_categories = [
        ADMINISTRATION_CATEGORY,
        NAVIGATION_CATEGORY,
        HOW_TO_CONTRIBUTE_CATEGORY,
    ]

    total = Document.objects.visible(
        user,
        locale=settings.WIKI_DEFAULT_LANGUAGE,
        is_archived=False,
        is_localizable=True,
        current_revision__isnull=False,
        latest_localizable_revision__isnull=False,
    ).exclude(html__startswith=REDIRECT_HTML)

    if product:
        total = total.filter(products=product)
        if not product.questions_enabled(locale):
            # The product does not have a forum for this locale.
            ignore_categories.append(CANNED_RESPONSES_CATEGORY)

    total = total.exclude(category__in=ignore_categories)

    total_docs = total.filter(is_template=False).count()
    total_templates = total.filter(is_template=True).count()

    # Translations whose based_on revision has no >10-significance, ready-for-
    # l10n revisions after it.

    any_significant_updates_exist = Exists(
        Revision.objects.filter(
            document=OuterRef("parent"),
            is_ready_for_localization=True,
            significance__gte=MEDIUM_SIGNIFICANCE,
            id__gt=OuterRef("current_revision__based_on__id"),
        )
    )

    up_to_date_translation_count = (
        Document.objects.visible(
            user,
            locale=locale,
            is_archived=False,
            parent__isnull=False,
            parent__is_archived=False,
            parent__is_localizable=True,
            current_revision__isnull=False,
            parent__latest_localizable_revision__isnull=False,
        )
        .exclude(parent__category__in=ignore_categories)
        .exclude(parent__html__startswith=REDIRECT_HTML)
        .exclude(any_significant_updates_exist)
    )

    if product:
        up_to_date_translation_count = up_to_date_translation_count.filter(
            parent__products=product
        )

    translated_docs = up_to_date_translation_count.filter(is_template=False).count()
    translated_templates = up_to_date_translation_count.filter(is_template=True).count()

    top_n_query = (
        Document.objects.visible(
            user,
            locale=settings.WIKI_DEFAULT_LANGUAGE,
            is_archived=False,
            is_template=False,
            is_localizable=True,
            parent__isnull=True,
            current_revision__isnull=False,
            latest_localizable_revision__isnull=False,
        )
        .exclude(category__in=ignore_categories)
        .exclude(html__startswith=REDIRECT_HTML)
    )

    if product:
        top_n_query = top_n_query.filter(products=product)

    top_n_query = (
        top_n_query.annotate(
            is_translated=Exists(
                Document.objects.filter(
                    locale=locale,
                    parent=OuterRef("pk"),
                    current_revision__isnull=False,
                )
                .filter(
                    Exists(
                        Revision.objects.filter(document=OuterRef("pk")).filter(
                            Q(is_approved=True) | Q(reviewed__isnull=True)
                        )
                    )
                )
                .exclude(any_significant_updates_exist)
            )
        )
        .alias(num_visits=get_visits_subquery())
        .order_by(F("num_visits").desc(nulls_last=True), "title")
    )

    top_20_translated = top_n_query[:20].aggregate(
        num_translated=Count("pk", filter=Q(is_translated=True))
    )["num_translated"]

    top_50_translated = top_n_query[:50].aggregate(
        num_translated=Count("pk", filter=Q(is_translated=True))
    )["num_translated"]

    top_100_translated = top_n_query[:100].aggregate(
        num_translated=Count("pk", filter=Q(is_translated=True))
    )["num_translated"]

    return {
        "top-20": {
            # L10n: This is an entry header for the Overview table, displayed on
            # https://support.mozilla.org/localization (for non-en-US locales).
            "title": _("Top 20 Articles"),
            "numerator": top_20_translated,
            "denominator": 20 if total_docs > 20 else total_docs,
            "percent": percent_or_100(top_20_translated, 20 if total_docs > 20 else total_docs),
            # L10n: This is an entry description for the Overview table, displayed on
            # https://support.mozilla.org/localization (for non-en-US locales).
            "description": _("These are the top 20 most visited articles in the last 30 days, which account for over 50% of the traffic to the Knowledge Base."),
        },
        "top-50": {
            # L10n: This is an entry header for the Overview table, displayed on
            # https://support.mozilla.org/localization (for non-en-US locales).
            "title": _("Top 50 Articles"),
            "numerator": top_50_translated,
            "denominator": 50 if total_docs > 50 else total_docs,
            "percent": percent_or_100(top_50_translated, 50 if total_docs > 50 else total_docs),
            # L10n: This is an entry description for the Overview table, displayed on
            # https://support.mozilla.org/localization (for non-en-US locales).
            "description": _("These are the top 50 most visited articles " "in the last 30 days."),
        },
        "top-100": {
            # L10n: This is an entry header for the Overview table, displayed on
            # https://support.mozilla.org/localization (for non-en-US locales).
            "title": _("Top 100 Articles"),
            "numerator": top_100_translated,
            "denominator": 100 if total_docs > 100 else total_docs,
            "percent": percent_or_100(top_100_translated, 100 if total_docs > 100 else total_docs),
            # L10n: This is an entry description for the Overview table, displayed on
            # https://support.mozilla.org/localization (for non-en-US locales).
            "description": _("These are the top 100 most visited articles in the last 30 days, which account for over 99% of the traffic to the Knowledge Base."),
        },
        "templates": {
            # This string is reused in different contexts, so we should avoid providing an l10n comment.
            "title": _("Templates"),
            "url": "#" + TemplateTranslationsReadout.slug,
            "numerator": translated_templates,
            "denominator": total_templates,
            "percent": percent_or_100(translated_templates, total_templates),
            # L10n: This is an entry description for the Overview table, displayed on
            # https://support.mozilla.org/localization (for non-en-US locales).
            "description": _("Templates are a way of reusing pieces of content across KB articles. You can create and update a set of instructions in one place, and then refer to it in other pages."),
        },
        "all": {
            # L10n: This is an entry header for the Overview table, displayed on
            # https://support.mozilla.org/localization (for non-en-US locales).
            "title": _("All Knowledge Base Articles"),
            "numerator": translated_docs,
            "denominator": total_docs,
            "percent": percent_or_100(translated_docs, total_docs),
            # L10n: This is an entry description for the Overview table, displayed on
            # https://support.mozilla.org/localization (for non-en-US locales).
            "description": _("This is the number of all Knowledge Base articles that are ready to be localized."),
        },
    }


class Readout:
    """Abstract class representing one table on the Localization Dashboard

    Describing these as atoms gives us the whole-page details views for free.

    """

    # title = _lazy(u'Title of Readout')
    # description = _lazy(u'Paragraph of explanation')
    # short_title= = _lazy(u'Short Title of Readout for In-Page Links')
    # slug = 'Unique URL slug for detail page'
    # details_link_text = _lazy(u'All articles from this readout...')

    # L10n: This is a column header for an abstract Localization Dashboard table. It refers to articles.
    column3_label = _lazy("Visits in last 30 days")
    # This string is reused in different contexts, so we should avoid providing an l10n comment.
    column4_label = _lazy("Status")
    modes = [
        # L10n: This is a sorting option for an abstract Localization Dashboard table. It refers to articles.
        (MOST_VIEWED, _lazy("Most Viewed")),
        # L10n: This is a sorting option for an abstract Localization Dashboard table. It refers to articles.
        (MOST_RECENT, _lazy("Most Recent")),
    ]
    default_mode: int | None = MOST_VIEWED

    def __init__(self, request, locale=None, mode=None, product=None):
        """Take request so the template can use contextual macros that need it.

        Renders the data for the locale specified by the request, but you can
        override it by passing another in `locale`.

        """
        self.request = request
        self.user = getattr(request, "user", None)
        self.locale = locale or request.LANGUAGE_CODE
        self.mode = mode if mode is not None else self.default_mode
        # self.mode is allowed to be invalid.
        self.product = product

    def rows(self, max=None):
        """Return an iterable of dicts containing the data for the table.

        This default implementation calls _query_and_params and row_to_dict.
        You can either implement those or, if you need more flexibility,
        override this.

        Limit to `max` rows.

        """
        return self.sort_and_truncate([self.row_to_dict(r) for r in self.get_queryset(max)], max)

    def render(self, max_rows=None, rows=None):
        """Return HTML table rows, optionally limiting to a number of rows."""
        # Fetch the rows if they aren't passed.
        if not rows:
            rows = self.rows(max_rows)

        # Compute percents for bar widths:
        max_visits = max(r["visits"] or 0 for r in rows) if rows else 0
        for r in rows:
            visits = r["visits"]
            r["percent"] = (
                0
                if visits is None or not max_visits
                else round(visits / float(max_visits) * 100)
            )

        # Render:
        return render_to_string(
            "dashboards/includes/kb_readout.html",
            {
                "rows": rows,
                "column3_label": self.column3_label,
                "column4_label": self.column4_label,
            },
            request=self.request,
        )

    @classmethod
    def should_show_to(cls, request):
        """Whether this readout should be shown on the request."""
        return True

    def get_queryset(self, max):
        """Return a tuple: (query, params to bind it to)."""
        raise NotImplementedError

    def row_to_dict(self, row):
        """Turn a DB row tuple into a dict for the template."""
        raise NotImplementedError

    def sort_and_truncate(self, rows, max):
        """Allows a readout to sort and truncate the rows list

        This happens after generating the row structures which starts
        with what we get back from SQL and incorporates row_to_dict
        and before we render the rows to output.

        :arg rows: the list of rows to sort
        :arg max: the index at which to truncate
        """
        return rows

    def get_absolute_url(self, locale, product=None):
        if self.slug in L10N_READOUTS:
            url = reverse(
                "dashboards.localization_detail", kwargs={"readout_slug": self.slug}, locale=locale
            )
        elif self.slug in CONTRIBUTOR_READOUTS:
            url = reverse(
                "dashboards.contributors_detail", kwargs={"readout_slug": self.slug}, locale=locale
            )
        else:
            raise KeyError("This Readout was not found: {}".format(self.slug))

        if product:
            return urlparams(url, product=product.slug)

        return url


class MostVisitedDefaultLanguageReadout(Readout):
    """Most-Visited readout for the default language"""

    # L10n: This refers to articles.
    title = _lazy("Most Visited")
    # No short_title; the Contributors dash lacks an Overview readout
    # L10n: Unused. A link to be displayed under the Most Visited overview table,
    # which redirects users to the full Most Visited table (https://support.mozilla.org/contributors/most-visited).
    details_link_text = _lazy("All knowledge base articles...")
    slug = "most-visited"
    # L10n: This is a table column header that refers to article visit count.
    column3_label = _lazy("Visits")
    modes = PERIODS
    default_mode = LAST_30_DAYS

    def get_queryset(self, max=None):
        if self.mode in {m[0] for m in self.modes}:
            period = self.mode
        else:
            period = self.default_mode

        qs = (
            Document.objects.visible(
                self.user,
                locale=self.locale,
                is_archived=False,
                is_template=False,
            )
            .exclude(
                category__in=(
                    NAVIGATION_CATEGORY,
                    ADMINISTRATION_CATEGORY,
                    CANNED_RESPONSES_CATEGORY,
                    HOW_TO_CONTRIBUTE_CATEGORY,
                )
            )
            .exclude(html__startswith=REDIRECT_HTML)
        )

        if self.product:
            qs = qs.filter(products=self.product)

        qs = (
            qs.annotate(
                needs_review=Exists(
                    Revision.objects.filter(
                        document=OuterRef("pk"),
                        reviewed__isnull=True,
                        id__gt=OuterRef("current_revision__id"),
                    )
                )
            )
            .annotate(num_visits=get_visits_subquery(period=period))
            .order_by(F("num_visits").desc(nulls_last=True), "title")
        )

        if max:
            qs = qs[:max]

        return qs.values_list("slug", "title", "num_visits", "needs_review")

    def row_to_dict(self, row):
        (slug, title, visits, needs_review) = row
        status, view_name, dummy = REVIEW_STATUSES[needs_review]
        return {
            "title": title,
            "url": reverse("wiki.document", args=[slug], locale=self.locale),
            "visits": visits,
            "status": status,
            "status_url": reverse(view_name, args=[slug], locale=self.locale) if view_name else "",
        }


class CategoryReadout(Readout):
    """Abstract class representing a readout ordered by visits and intended
    to be filtered by category."""

    # L10n: This is a table column header that refers to article visit count.
    column3_label = _lazy("Visits")
    modes = []
    default_mode = None
    filter_kwargs: dict[str, bool | int] = {}

    def get_queryset(self, max=None):
        if self.mode in {m[0] for m in self.modes}:
            period = self.mode
        else:
            period = self.default_mode

        qs = Document.objects.visible(
            self.user,
            locale=self.locale,
            is_archived=False,
            **self.filter_kwargs,
        ).exclude(html__startswith=REDIRECT_HTML)

        if self.product:
            qs = qs.filter(products=self.product)

        qs = qs.annotate(
            needs_review=Exists(
                Revision.objects.filter(document=OuterRef("pk"), reviewed__isnull=True).filter(
                    Q(id__gt=F("document__current_revision__id"))
                    | Q(document__current_revision__isnull=True)
                )
            ),
            unready_for_l10n=Exists(
                Revision.objects.filter(
                    document=OuterRef("pk"),
                    is_approved=True,
                    is_ready_for_localization=False,
                )
                .filter(
                    Q(id__gt=F("document__latest_localizable_revision__id"))
                    | Q(document__latest_localizable_revision__isnull=True)
                )
                .filter(Q(significance__gt=TYPO_SIGNIFICANCE) | Q(significance__isnull=True))
            ),
            num_visits=get_visits_subquery(period=period),
        ).order_by(F("num_visits").desc(nulls_last=True), "title")

        if max:
            qs = qs[:max]

        return qs.values_list(
            "slug", "title", "num_visits", "needs_change", "needs_review", "unready_for_l10n"
        )

    def row_to_dict(self, row):
        (slug, title, visits, needs_changes, needs_review, unready_for_l10n) = row
        if needs_review:
            status, view_name, _ = REVIEW_STATUSES[needs_review]
        elif needs_changes:
            # L10n: This is a KB article status. It may be displayed on
            # https://support.mozilla.org/localization#template-translations,
            # https://support.mozilla.org/contributors/templates,
            # https://support.mozilla.org/contributors/how-to-contribute or
            # https://support.mozilla.org/contributors/administration.
            status = _lazy("Changes Needed")
            view_name = "wiki.document_revisions"
        elif unready_for_l10n:
            # L10n: This refers to articles.
            status = _lazy("Changes Not Ready For Localization")
            view_name = "wiki.document_revisions"
        else:
            status, view_name, _ = REVIEW_STATUSES[0]

        return {
            "title": title,
            "url": reverse("wiki.document", args=[slug], locale=self.locale),
            "visits": visits,
            "status": status,
            "status_url": reverse(view_name, args=[slug], locale=self.locale) if view_name else "",
        }


class TemplateReadout(CategoryReadout):
    # This string is reused in different contexts, so we should avoid providing an l10n comment.
    title = _lazy("Templates")
    slug = "templates"
    # The following l10n comment duplicates a comment from a different context.
    # We can do that since the string is not displayed at all for this class.
    # L10n: This is a link displayed under the Templates overview table
    # (https://support.mozilla.org/localization#template-translations for non-en-US locales),
    # which redirects users to the full Templates table (https://support.mozilla.org/localization/template-translations).
    details_link_text = _lazy("All templates...")
    filter_kwargs = {"is_template": True}


class HowToContributeReadout(CategoryReadout):
    # L10n: This is a table header displayed on
    # https://support.mozilla.org/contributors/how-to-contribute. It refers to the article topic.
    title = _lazy("How To Contribute")
    slug = "how-to-contribute"
    # L10n: Unused. A link to be displayed under the How To Contribute overview table,
    # which redirects users to the full How To Contribute table.
    details_link_text = _lazy("All How To Contribute articles...")
    filter_kwargs = {"category": HOW_TO_CONTRIBUTE_CATEGORY}


class AdministrationReadout(CategoryReadout):
    # L10n: This is a table header displayed on
    # https://support.mozilla.org/contributors/administration. It refers to the article topic.
    title = _lazy("Administration")
    slug = "administration"
    # L10n: Unused. A link to be displayed under the Administration overview table,
    # which redirects users to the full Administration table.
    details_link_text = _lazy("All Administration articles...")
    filter_kwargs = {"category": ADMINISTRATION_CATEGORY}


class MostVisitedTranslationsReadout(MostVisitedDefaultLanguageReadout):
    """Most-Visited readout for non-default languages

    Adds a few subqueries to determine the status of translations.

    Shows the articles that are most visited in English, even if there are no
    translations of those articles yet. This draws attention to articles that
    we should drop everything to translate.

    """

    # L10n: This refers to articles.
    short_title = _lazy("Most Visited")
    slug = "most-visited-translations"
    # L10n: This is a link displayed under the Most Visited overview table
    # (https://support.mozilla.org/uk/localization#most-visited-translations for non-en-US locales),
    # which redirects users to the full Most Visited table
    # (https://support.mozilla.org/localization/most-visited-translations for non-en-US locales).
    details_link_text = _lazy("All translations...")

    def get_queryset(self, max=None):
        if self.mode in {m[0] for m in self.modes}:
            period = self.mode
        else:
            period = self.default_mode

        ignore_categories = [
            NAVIGATION_CATEGORY,
            ADMINISTRATION_CATEGORY,
            HOW_TO_CONTRIBUTE_CATEGORY,
        ]

        qs = (
            Document.objects.visible(
                self.user,
                locale=settings.WIKI_DEFAULT_LANGUAGE,
                is_archived=False,
                is_localizable=True,
                parent__isnull=True,
                latest_localizable_revision__isnull=False,
            )
            .exclude(html__startswith=REDIRECT_HTML)
            .filter(
                no_translation_exists(self.locale)
                | visible_translation_exists(self.user, self.locale)
            )
        )

        if self.product:
            qs = qs.filter(products=self.product)
            if not self.product.questions_enabled(locale=self.locale):
                # The product does not have a forum for this locale.
                ignore_categories.append(CANNED_RESPONSES_CATEGORY)

        transdoc_subquery = Document.objects.filter(
            locale=self.locale,
            parent=OuterRef("pk"),
        ).filter(
            Exists(
                Revision.objects.filter(document=OuterRef("pk")).filter(
                    Q(is_approved=True) | Q(reviewed__isnull=True)
                )
            )
        )

        qs = (
            qs.exclude(category__in=ignore_categories)
            .annotate(
                transdoc_slug=Subquery(transdoc_subquery.values("slug")),
                transdoc_title=Subquery(transdoc_subquery.values("title")),
                transdoc_current_revision_based_on_id=Subquery(
                    transdoc_subquery.values("current_revision__based_on__id")
                ),
                needs_review=Exists(
                    Revision.objects.filter(
                        document__parent=OuterRef("pk"),
                        document__locale=self.locale,
                        reviewed__isnull=True,
                    ).filter(
                        Q(id__gt=F("document__current_revision__id"))
                        | Q(document__current_revision__isnull=True),
                    )
                ),
            )
            .annotate(most_significant_change=MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE_SUBQUERY)
            .annotate(num_visits=get_visits_subquery(period=period))
            .order_by(F("num_visits").desc(nulls_last=True), Coalesce("transdoc_title", "title"))
        )

        if max:
            qs = qs[:max]

        return qs.values_list(
            "slug",
            "title",
            "transdoc_slug",
            "transdoc_title",
            "num_visits",
            "most_significant_change",
            "needs_review",
        )

    def row_to_dict(self, columns):
        return row_to_dict_with_out_of_dateness(self.locale, *columns)

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
            rows = [x for x in rows if x["status_class"] != "ok"]
            rows = rows[:max_rows]

        return super().render(rows=rows)


class TemplateTranslationsReadout(Readout):
    """Readout for templates in non-default languages

    Shows the templates even if there are no translations of them yet.
    This draws attention to templates that we should drop everything to
    translate.

    """

    # This string is reused in different contexts, so we should avoid providing an l10n comment.
    title = _lazy("Templates")
    short_title = _lazy("Templates")
    slug = "template-translations"
    # L10n: This is a link displayed under the Templates overview table
    # (https://support.mozilla.org/localization#template-translations for non-en-US locales),
    # which redirects users to the full Templates table (https://support.mozilla.org/localization/template-translations).
    details_link_text = _lazy("All templates...")
    column3_label = ""
    modes = []
    default_mode = None

    def get_queryset(self, max=None):
        qs = (
            Document.objects.visible(
                self.user,
                locale=settings.WIKI_DEFAULT_LANGUAGE,
                is_template=True,
                is_archived=False,
                is_localizable=True,
                parent__isnull=True,
                latest_localizable_revision__isnull=False,
            )
            .exclude(html__startswith=REDIRECT_HTML)
            .filter(
                no_translation_exists(self.locale)
                | visible_translation_exists(self.user, self.locale)
            )
        )

        if self.product:
            qs = qs.filter(products=self.product)

        transdoc_subquery = Document.objects.filter(
            locale=self.locale,
            parent=OuterRef("pk"),
        )

        qs = qs.annotate(
            transdoc_slug=Subquery(transdoc_subquery.values("slug")),
            transdoc_title=Subquery(transdoc_subquery.values("title")),
            transdoc_current_revision_based_on_id=Subquery(
                transdoc_subquery.values("current_revision__based_on__id")
            ),
            needs_review=Exists(
                Revision.objects.filter(
                    document__parent=OuterRef("pk"),
                    document__locale=self.locale,
                    reviewed__isnull=True,
                ).filter(
                    Q(id__gt=F("document__current_revision__id"))
                    | Q(document__current_revision__isnull=True),
                )
            ),
        ).annotate(most_significant_change=MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE_SUBQUERY)

        return qs.values_list(
            "slug",
            "title",
            "transdoc_slug",
            "transdoc_title",
            "most_significant_change",
            "needs_review",
        )

    def row_to_dict(self, row):
        (eng_slug, eng_title, slug, title, significance, needs_review) = row
        return row_to_dict_with_out_of_dateness(
            self.locale, eng_slug, eng_title, slug, title, None, significance, needs_review
        )

    def sort_and_truncate(self, rows, max):
        # Bubble the "update needed" templates to the top, but otherwise
        # keep it ordered by title.
        #
        # As a little side note, 'status' here is either an empty
        # string or a _lazy translation of 'Update Needed'. So if it's
        # an empty string, then the equality is True and True in
        # Python is 1 and 1 comes after 0... Therefore, False comes
        # first in ordering.
        rows.sort(key=lambda row: (row["status"] == "", row["status_class"], row["title"]))
        return rows[:max]


class UnreviewedReadout(Readout):
    # L10n: This is a table header displayed on
    # https://support.mozilla.org/localization#unreviewed (for non-en-US locales)
    # and https://support.mozilla.org/localization/unreviewed.
    # It refers not just to changes to translations but also to unreviewed changes to
    # docs in this locale that are not translations.
    title = _lazy("Unreviewed Changes")

    # L10n: Unused. This is a short name for the Unreviewed Changes table,
    # displayed on https://support.mozilla.org/localization#unreviewed (for non-en-US locales)
    # and https://support.mozilla.org/localization/unreviewed.
    # It refers not just to changes to translations but also to unreviewed changes to
    # docs in this locale that are not translations.
    short_title = pgettext_lazy("document", "Unreviewed")
    # L10n: This is a link displayed under the Unreviewed Changes overview table
    # (https://support.mozilla.org/localization#unreviewed for non-en-US locales),
    # which redirects users to the full Unreviewed Changes table (https://support.mozilla.org/localization/unreviewed).
    details_link_text = _lazy("All articles requiring review...")
    slug = "unreviewed"
    # L10n: This is a column header for the Unreviewed Changes table, displayed on
    # https://support.mozilla.org/localization#unreviewed (for non-en-US locales)
    # and https://support.mozilla.org/localization/unreviewed.
    # It refers to the time an article was last changed.
    column4_label = _lazy("Changed")

    def get_queryset(self, max=None):
        prefix = "" if self.locale == settings.WIKI_DEFAULT_LANGUAGE else "parent__"

        if self.mode == MOST_RECENT:
            order_by_args = ("-max_created",)
        else:
            order_by_args = (F("num_visits").desc(nulls_last=True), "title")

        qs = (
            Revision.objects.visible(
                self.user,
                reviewed__isnull=True,
                document__locale=self.locale,
                **{f"document__{prefix}is_archived": False},
            )
            .filter(
                Q(id__gt=F("document__current_revision__id"))
                | Q(document__current_revision__isnull=True)
            )
            .exclude(**{f"document__{prefix}html__startswith": REDIRECT_HTML})
        )

        if self.product:
            qs = qs.filter(**{f"document__{prefix}products": self.product})

        qs = (
            qs.order_by()
            .values("document")
            .annotate(
                slug=F("document__slug"),
                title=F("document__title"),
                max_created=Max("created"),
                usernames=StringAgg(
                    "creator__username",
                    delimiter=", ",
                    distinct=True,
                    ordering="creator__username",
                ),
                num_visits=get_visits_subquery(document=OuterRef("document")),
            )
            .order_by(*order_by_args)
        )

        if max:
            qs = qs[:max]

        return qs.values_list("slug", "title", "max_created", "usernames", "num_visits")

    def row_to_dict(self, row):
        (slug, title, changed, users, visits) = row
        return {
            "title": title,
            "url": reverse("wiki.document_revisions", args=[slug], locale=self.locale),
            "visits": visits,
            "updated": changed,
            "users": users,
        }


class UnhelpfulReadout(Readout):
    # L10n: This is a table header displayed on https://support.mozilla.org/contributors/unhelpful.
    title = _lazy("Unhelpful Documents")

    # L10n: Unused. This is a short name for the Unhelpful Documents table,
    # displayed on https://support.mozilla.org/contributors/unhelpful.
    short_title = pgettext_lazy("document", "Unhelpful")
    # L10n: Unused. This is a link to be displayed under the Unhelpful Documents overview table,
    # which redirects users to the full Unhelpful Documents table (https://support.mozilla.org/contributors/unhelpful).
    details_link_text = _lazy("All unhelpful articles...")
    slug = "unhelpful"
    # L10n: This is a column header for the Unhelpful Documents table, displayed on
    # https://support.mozilla.org/contributors/unhelpful.
    # It refers to the article's helpful/unhelpful vote count.
    column3_label = _lazy("Total Votes")
    # L10n: This is a column header for the Unhelpful Documents table, displayed on
    # https://support.mozilla.org/contributors/unhelpful.
    # It refers to the article's helpful vote percentage (out of total helpful/unhelpful vote count).
    column4_label = _lazy("Helpfulness")
    modes = []
    default_mode = None

    # This class is a namespace and doesn't get instantiated.
    key = settings.HELPFULVOTES_UNHELPFUL_KEY
    try:
        hide_readout = redis_client("helpfulvotes").llen(key) == 0
    except RedisError as e:
        log.error("Redis error: {}".format(e))
        hide_readout = True

    def rows(self, max=None):
        REDIS_KEY = settings.HELPFULVOTES_UNHELPFUL_KEY
        try:
            redis = redis_client("helpfulvotes")
            length = redis.llen(REDIS_KEY)
            max_get = max or length
            output = redis.lrange(REDIS_KEY, 0, max_get)
        except RedisError as e:
            log.error("Redis error: {}".format(e))
            output = []

        data = []
        for r in output:
            row = self.row_to_dict(r)
            if row:
                data.append(row)

        return data

    def row_to_dict(self, strresult):
        result = strresult.split("::")

        # Filter by product
        if self.product:
            doc = Document.objects.filter(products__in=[self.product], slug=result[5])
            if not doc.count():
                return None

        helpfulness = Markup(
            '<span title="{:+.1f}%">{:.1f}%</span>'.format(float(result[3]) * 100, float(result[2]) * 100)
        )
        return {
            "title": str(result[6]),
            "url": reverse("wiki.document_revisions", args=[result[5]], locale=self.locale),
            "visits": int(float(result[1])),
            "custom": True,
            "column4_data": helpfulness,
        }


class UnreadyForLocalizationReadout(Readout):
    """Articles which have approved but unready revisions newer than their
    latest ready-for-l10n ones"""

    # L10n: This refers to articles.
    title = _lazy("Changes Not Ready For Localization")
    # L10n: Unused. This is a description for the Changes Not Ready For Localization table,
    # displayed on https://support.mozilla.org/contributors/unready.
    description = _lazy("Articles which have approved revisions newer than the latest ready-for-localization one")
    # No short_title; the Contributors dash lacks an Overview readout
    # L10n: Unused. This is a link to be displayed under the Changes Not Ready For Localization overview table,
    # which redirects users to the full Changes Not Ready For Localization table (https://support.mozilla.org/contributors/unready).
    details_link_text = _lazy("All articles with changes not ready for localization...")
    slug = "unready"
    # L10n: This refers to article revisions.
    column4_label = _lazy("Approved")

    def get_queryset(self, max=None):
        if self.mode == MOST_RECENT:
            order_by_args = (F("max_reviewed").desc(nulls_last=True),)
        else:
            order_by_args = (F("num_visits").desc(nulls_last=True), "title")

        qs = (
            Revision.objects.visible(
                self.user,
                is_approved=True,
                is_ready_for_localization=False,
                document__locale=settings.WIKI_DEFAULT_LANGUAGE,
                document__is_archived=False,
                document__is_localizable=True,
            )
            .exclude(document__html__startswith=REDIRECT_HTML)
            .filter(Q(significance__gt=TYPO_SIGNIFICANCE) | Q(significance__isnull=True))
            .filter(
                Q(id__gt=F("document__latest_localizable_revision__id"))
                | Q(document__latest_localizable_revision__isnull=True)
            )
            .filter(
                Q(
                    document__current_revision__id__gt=F(
                        "document__latest_localizable_revision__id"
                    )
                )
                | Q(document__latest_localizable_revision__isnull=True)
            )
        )

        if self.product:
            qs = qs.filter(document__products=self.product)

        qs = (
            qs.order_by()
            .values("document")
            .annotate(
                slug=F("document__slug"),
                title=F("document__title"),
                max_reviewed=Max("reviewed"),
                num_visits=get_visits_subquery(document=OuterRef("document")),
            )
            .order_by(*order_by_args)
        )

        if max:
            qs = qs[:max]

        return qs.values_list("slug", "title", "max_reviewed", "num_visits")

    def row_to_dict(self, row):
        (slug, title, reviewed, visits) = row
        return {
            "title": title,
            "url": reverse(
                "wiki.document_revisions", args=[slug], locale=settings.WIKI_DEFAULT_LANGUAGE
            ),
            "visits": visits,
            "updated": reviewed,
        }


class NeedsChangesReadout(Readout):
    """Articles which need change."""

    # L10n: This is a table header displayed on https://support.mozilla.org/contributors/need-changes.
    title = _lazy("Need Changes")
    # L10n: Unused. This is a description for the Need Changes table,
    # displayed on https://support.mozilla.org/contributors/need-changes.
    description = _lazy("Articles that require changes.")
    # No short_title; the Contributors dash lacks an Overview readout
    # L10n: Unused. This is a link to be displayed under the Need Changes overview table,
    # which redirects users to the full Need Changes table (https://support.mozilla.org/contributors/need-changes).
    details_link_text = _lazy("All articles that require changes...")
    slug = "need-changes"
    # L10n: A noun. There are comments for articles in general (on https://support.mozilla.org/contributors/need-changes) and every article revision.
    column4_label = _lazy("Comment")

    def get_queryset(self, max=None):
        qs = Document.objects.visible(
            self.user,
            locale=settings.WIKI_DEFAULT_LANGUAGE,
            is_archived=False,
            needs_change=True,
            parent__isnull=True,
        ).exclude(html__startswith=REDIRECT_HTML)

        if self.product:
            qs = qs.filter(products=self.product)

        qs = qs.annotate(num_visits=get_visits_subquery()).order_by(
            F("num_visits").desc(nulls_last=True), "title"
        )

        if max:
            qs = qs[:max]

        return qs.values_list("slug", "title", "needs_change_comment", "num_visits")

    def row_to_dict(self, row):
        (slug, title, comment, visits) = row
        return {
            "title": title,
            "url": reverse(
                "wiki.document_revisions", args=[slug], locale=settings.WIKI_DEFAULT_LANGUAGE
            ),
            "visits": visits,
            "custom": True,
            "column4_data": comment,
        }


class CannedResponsesReadout(Readout):
    # This string is reused in different contexts, so we should avoid providing an l10n comment.
    title = _lazy("Canned Responses")
    # L10n: Unused. This is a description for the Canned Responses table.
    description = _lazy("Localization status of all canned responses")
    slug = "canned-responses"
    # L10n: Unused. This is a link to be displayed under the Canned Responses overview table,
    # which redirects users to the full Canned Responses table.
    details_link_text = _lazy("All canned responses articles...")

    @classmethod
    def should_show_to(cls, request):
        return request.LANGUAGE_CODE in AAQConfig.objects.locales_list()

    def get_queryset(self, max=None):
        qs = (
            Document.objects.visible(
                self.user,
                locale=settings.WIKI_DEFAULT_LANGUAGE,
                is_archived=False,
                parent__isnull=True,
                category=CANNED_RESPONSES_CATEGORY,
            )
            .exclude(html__startswith=REDIRECT_HTML)
            .filter(
                no_translation_exists(self.locale)
                | visible_translation_exists(self.user, self.locale)
            )
        )

        if self.product:
            qs = qs.filter(products=self.product)

        transdoc_subquery = Document.objects.filter(
            locale=self.locale,
            parent=OuterRef("pk"),
        )

        qs = (
            qs.annotate(
                transdoc_slug=Subquery(transdoc_subquery.values("slug")),
                transdoc_title=Subquery(transdoc_subquery.values("title")),
                transdoc_current_revision_based_on_id=Subquery(
                    transdoc_subquery.values("current_revision__based_on__id")
                ),
                needs_review=Exists(
                    Revision.objects.filter(
                        document__parent=OuterRef("pk"),
                        document__locale=self.locale,
                        reviewed__isnull=True,
                    ).filter(
                        Q(id__gt=F("document__current_revision__id"))
                        | Q(document__current_revision__isnull=True),
                    )
                ),
                num_visits=get_visits_subquery(),
            )
            .annotate(most_significant_change=MOST_SIGNIFICANT_CHANGE_READY_TO_TRANSLATE_SUBQUERY)
            .order_by(F("num_visits").desc(nulls_last=True), Coalesce("transdoc_title", "title"))
        )

        if max:
            qs = qs[:max]

        return qs.values_list(
            "slug",
            "title",
            "transdoc_slug",
            "transdoc_title",
            "num_visits",
            "most_significant_change",
            "needs_review",
        )

    def row_to_dict(self, row):
        return row_to_dict_with_out_of_dateness(self.locale, *row)


# L10n Dashboard tables that have their own whole-page views:
L10N_READOUTS = OrderedDict(
    (t.slug, t)  # type: ignore
    for t in [MostVisitedTranslationsReadout, UnreviewedReadout, TemplateTranslationsReadout]
)

# Contributors ones:
CONTRIBUTOR_READOUTS = OrderedDict(
    (t.slug, t)  # type: ignore
    for t in [
        MostVisitedDefaultLanguageReadout,
        TemplateReadout,
        HowToContributeReadout,
        AdministrationReadout,
        UnreviewedReadout,
        NeedsChangesReadout,
        UnreadyForLocalizationReadout,
        UnhelpfulReadout,
    ]
)

# All:
READOUTS = L10N_READOUTS.copy()
READOUTS.update(CONTRIBUTOR_READOUTS)

GROUP_L10N_READOUTS = OrderedDict(
    (t.slug, t) for t in [MostVisitedTranslationsReadout, UnreviewedReadout]  # type: ignore
)
# English group locale is the same as l10n dashboard.
GROUP_CONTRIBUTOR_READOUTS = CONTRIBUTOR_READOUTS
