from datetime import datetime
from functools import cache

from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, Exists, F, OuterRef, Q, Value
from django.db.models.functions import Now

from kitsune.dashboards.readouts import get_visits_subquery
from kitsune.l10n.llm import get_localization
from kitsune.l10n.models import RevisionActivityRecord
from kitsune.l10n.utils import duration_to_text, get_l10n_bot
from kitsune.wiki.models import Document, Locale, Revision
from kitsune.wiki.config import REDIRECT_HTML


def is_suitable_for_l10n(doc):
    """
    Returns a boolean indicating whether the given document is a default
    document, localizable, has a current revision, and has a localizable
    revision. In other words, are the bare minimum fundamentals in place
    to be suitable for localization.
    """
    return (
        doc
        and (doc.locale == settings.WIKI_DEFAULT_LANGUAGE)
        and doc.is_localizable
        and doc.current_revision
        and doc.latest_localizable_revision
    )


def is_allowed_for_machine_translation(mt_config, doc):
    """
    Returns a boolean indicating whether the document is allowed for machine translation.
    """
    if doc.locale != settings.WIKI_DEFAULT_LANGUAGE:
        if not (doc.parent and (doc.locale in mt_config.enabled_languages)):
            return False
        doc = doc.parent

    return (
        is_suitable_for_l10n(doc)
        and not doc.is_archived
        and not doc.html.startswith(REDIRECT_HTML)
        and mt_config.is_slug_allowed(doc.slug)
        and mt_config.is_approved_date_allowed(doc.latest_localizable_revision.reviewed)
        and mt_config.is_approver_allowed(doc.latest_localizable_revision.reviewer)
    )


@cache
def has_inactive_team(locale, grace_period):
    """
    Returns a boolean indicating whether or not the given locale has a
    team without an active leader or reviewer within the grace period.
    """
    return not (
        Locale.objects.filter(locale=locale)
        .filter(
            Exists(
                Revision.objects.filter(
                    (
                        (Q(creator__in=OuterRef("leaders")) | Q(creator__in=OuterRef("reviewers")))
                        & Q(created__gt=Now() - grace_period)
                    )
                    | (
                        (
                            Q(reviewer__in=OuterRef("leaders"))
                            | Q(reviewer__in=OuterRef("reviewers"))
                        )
                        & Q(reviewed__gt=Now() - grace_period)
                    )
                )
            )
        )
        .exists()
    )


def current_revision_is_unreviewed_machine_translation(doc):
    """
    Convenience function that returns a boolean indicating whether or not
    the given document's current revision was machine-generated and not
    reviewed by a human.
    """
    if (
        (doc.locale == settings.WIKI_DEFAULT_LANGUAGE)
        or doc.parent is None
        or not (current_rev := doc.current_revision)
    ):
        return False
    l10n_bot = get_l10n_bot()
    return (current_rev.creator == l10n_bot) and (current_rev.reviewer == l10n_bot)


def create_machine_translations(mt_config, default_doc=None):
    """
    Create machine translations, within all locales enabled for machine translations,
    for the given default document if one is provided, otherwise all default documents.

    Returns a dict containing the URL's of the machine-translations that were created,
    organized by locale and the kind of creation.
    For example:
        {
            "it": {
                "awaiting_review": [...],
                "already_approved": [...],
            }
            "es": {
                "awaiting_review": [...],
                "already_approved": [...],
            },
            ...
        }
    """
    report = dict()

    if not mt_config.is_active():
        return report

    if default_doc and not is_allowed_for_machine_translation(mt_config, default_doc):
        return report

    def add_to_report(locale, rev):
        kind = "already_approved" if rev.is_approved else "awaiting_review"
        report.setdefault(locale, {}).setdefault(kind, []).append(rev.get_absolute_url())

    l10n_bot = get_l10n_bot()
    model_name = mt_config.llm_name
    enabled_locales = set(mt_config.enabled_languages)
    review_grace_period = mt_config.review_grace_period
    limit_to_approved_after = mt_config.limit_to_approved_after
    limit_to_approver_in_group = mt_config.limit_to_approver_in_group
    team_grace_period = mt_config.locale_team_inactivity_grace_period

    def get_filter_for(what, prefix=""):
        if what == "limit_to_slugs":
            full_slugs = mt_config.limit_to_full_slugs
            slug_prefixes = mt_config.limit_to_slug_prefixes
        else:
            full_slugs = mt_config.disabled_full_slugs
            slug_prefixes = mt_config.disabled_slug_prefixes
        filter = Q()
        if full_slugs:
            filter = Q(**{f"{prefix}slug__in": full_slugs})
        for p in slug_prefixes:
            filter |= Q(**{f"{prefix}slug__startswith": p})
        return filter

    # We want to cache the calls to "has_inactive_team" while creating machine
    # translations below, but always start with a fresh cache.
    has_inactive_team.cache_clear()

    if default_doc:
        qs_localized_docs = Document.objects.filter(parent=default_doc)
    else:
        qs_localized_docs = Document.objects.filter(
            parent__isnull=False,
            parent__is_archived=False,
            parent__is_localizable=True,
            parent__current_revision__isnull=False,
            parent__latest_localizable_revision__isnull=False,
        ).exclude(parent__html__startswith=REDIRECT_HTML)

        if slug_limiting := get_filter_for("limit_to_slugs", prefix="parent__"):
            qs_localized_docs = qs_localized_docs.filter(slug_limiting)

        if slug_disabling := get_filter_for("disabled_slugs", prefix="parent__"):
            qs_localized_docs = qs_localized_docs.exclude(slug_disabling)

        if limit_to_approved_after:
            qs_localized_docs = qs_localized_docs.filter(
                parent__latest_localizable_revision__reviewed__gt=limit_to_approved_after
            )

        if limit_to_approver_in_group:
            qs_localized_docs = qs_localized_docs.filter(
                parent__latest_localizable_revision__reviewer__groups=limit_to_approver_in_group
            )

    # Only consider localized documents within locales that have been enabled
    # for machine translations.
    qs_localized_docs = qs_localized_docs.filter(locale__in=enabled_locales)

    # First, let's find all localized documents that need a machine translation.
    for localized_doc in (
        qs_localized_docs.exclude(
            # Exclude localized documents that are already up-to-date with their parent.
            current_revision__based_on_id__gte=F("parent__latest_localizable_revision_id")
        )
        .exclude(
            # Exclude localized documents that already have an up-to-date revision
            # that is either machine-generated, or contributor-created but still
            # awaiting review within the review grace period.
            Exists(
                Revision.objects.filter(
                    document=OuterRef("pk"),
                ).filter(
                    Q(based_on_id__gte=OuterRef("parent__latest_localizable_revision_id"))
                    & (
                        Q(creator=l10n_bot)
                        | (Q(reviewed__isnull=True) & Q(created__gt=Now() - review_grace_period))
                    )
                )
            )
        )
        .annotate(
            num_visits=get_visits_subquery(document=OuterRef("pk")),
            num_visits_parent=get_visits_subquery(document=OuterRef("parent")),
        )
        .order_by(
            F("num_visits_parent").desc(nulls_last=True), F("num_visits").desc(nulls_last=True)
        )
        .select_related("parent")
    ):
        rev = create_machine_translation(
            model_name, localized_doc.parent, localized_doc.locale, l10n_bot, team_grace_period
        )
        add_to_report(localized_doc.locale, rev)

    # Finally, find all of the default documents that have a localizable revision but
    # don't yet have a localized document in one or more of the locales that have been
    # enabled for machine translation.
    if default_doc:
        existing_locales = set(qs_localized_docs.values_list("locale", flat=True))
        for locale in sorted(enabled_locales - existing_locales):
            rev = create_machine_translation(
                model_name, default_doc, locale, l10n_bot, team_grace_period
            )
            add_to_report(locale, rev)
    else:
        qs_default_docs = Document.objects.filter(
            is_archived=False,
            is_localizable=True,
            parent__isnull=True,
            current_revision__isnull=False,
            latest_localizable_revision__isnull=False,
            locale=settings.WIKI_DEFAULT_LANGUAGE,
        ).exclude(html__startswith=REDIRECT_HTML)

        if slug_limiting := get_filter_for("limit_to_slugs"):
            qs_default_docs = qs_default_docs.filter(slug_limiting)

        if slug_disabling := get_filter_for("disabled_slugs"):
            qs_default_docs = qs_default_docs.exclude(slug_disabling)

        if limit_to_approved_after:
            qs_default_docs = qs_default_docs.filter(
                latest_localizable_revision__reviewed__gt=limit_to_approved_after
            )

        if limit_to_approver_in_group:
            qs_default_docs = qs_default_docs.filter(
                latest_localizable_revision__reviewer__groups=limit_to_approver_in_group
            )

        for default_doc in (
            qs_default_docs.annotate(
                existing_locales=ArrayAgg(
                    "translations__locale",
                    filter=Q(translations__locale__in=enabled_locales),
                    default=Value([]),
                ),
                num_existing_locales=Count(
                    "translations__locale",
                    filter=Q(translations__locale__in=enabled_locales),
                ),
                num_visits=get_visits_subquery(document=OuterRef("pk")),
            )
            .filter(num_existing_locales__lt=len(enabled_locales))
            .order_by(F("num_visits").desc(nulls_last=True))
        ):
            for locale in sorted(enabled_locales - set(default_doc.existing_locales)):
                rev = create_machine_translation(
                    model_name, default_doc, locale, l10n_bot, team_grace_period
                )
                add_to_report(locale, rev)

    return report


def create_machine_translation(model_name, default_doc, target_locale, creator, team_grace_period):
    """
    Create and return the machine translation of the current revision of the given
    default document for the given target locale.
    """
    content = get_localization(model_name, default_doc, "content", target_locale)
    summary = get_localization(model_name, default_doc, "summary", target_locale)
    keywords = get_localization(model_name, default_doc, "keywords", target_locale)

    localized_doc = default_doc.translated_to(target_locale)

    if not localized_doc:
        if default_doc.is_template:
            # Do not translate the title of templates.
            title = default_doc.title
        else:
            title = get_localization(model_name, default_doc, "title", target_locale)

        # Create a new document for the locale if there isn't one already.
        localized_doc = Document.objects.create(
            title=title,
            parent=default_doc,
            locale=target_locale,
            slug=default_doc.slug,
            category=default_doc.category,
            allow_discussion=default_doc.allow_discussion,
        )

    now = datetime.now()

    extra_kwargs = {}
    if publish_now := has_inactive_team(target_locale, team_grace_period):
        extra_kwargs.update(
            reviewed=now,
            reviewer=creator,
            comment=(
                "Approved immediately because its locale team had not been "
                f"active within the past {duration_to_text(team_grace_period)}."
            ),
        )

    # Create the localized revision.
    rev = Revision.objects.create(
        created=now,
        creator=creator,
        content=content,
        summary=summary,
        keywords=keywords,
        document=localized_doc,
        is_approved=publish_now,
        based_on=default_doc.latest_localizable_revision,
        **extra_kwargs,
    )
    # Record the action.
    RevisionActivityRecord.objects.create(
        revision=rev,
        action=(
            RevisionActivityRecord.MT_CREATED_AS_APPROVED
            if publish_now
            else RevisionActivityRecord.MT_CREATED_AS_AWAITING_REVIEW
        ),
    )
    return rev


def manage_existing_machine_translations(mt_config, doc=None):
    """
    This function manages pending machine translations. It does two things,
    both of which operate within the context of the provided document if one
    is provided, otherwise all documents. First, it "cleans" pending machine
    translations, which means it marks as reviewed the machine translations
    that are either out-of-date or no longer needed. Second, it approves pending
    machine translations that are still relevant, and have either been awaiting
    review for longer than the review grace period, or have been rejected but no
    other translation has been approved within the post-review grace period.

    NOTE: This function will manage all existing machine translations, even
    those within locales that were initially enabled and then later disabled.

    Returns a dict containing the URL's of the machine-translated revisions
    that were modified, organized by locale and the kind of modification.
    For example:
        {
            "it": {
                "rejections": [...],
                "pre_review_approvals": [...],
                "post_rejection_approvals": [...],
            }
            "es": {
                "rejections": [...],
                "pre_review_approvals": [...],
                "post_rejection_approvals": [...],
            },
            ...
        }
    """
    l10n_bot = get_l10n_bot()
    review_grace_period = mt_config.review_grace_period
    post_review_grace_period = mt_config.post_review_grace_period

    report = dict()

    def add_to_report(locale, kind, rev):
        report.setdefault(locale, {}).setdefault(kind, []).append(rev.get_absolute_url())

    if doc:
        if not is_suitable_for_l10n(doc.original):
            return report
        if doc.locale == settings.WIKI_DEFAULT_LANGUAGE:
            # Consider the revisions of all of this document's localized documents.
            qs = Revision.objects.filter(document__parent=doc)
        else:
            # Only consider the revisions of this localized document.
            qs = doc.revisions
    else:
        # Consider the revisions of all localized documents.
        qs = Revision.objects.filter(
            document__parent__isnull=False,
            document__parent__is_localizable=True,
            document__parent__current_revision__isnull=False,
            document__parent__latest_localizable_revision__isnull=False,
        )

    qs = qs.filter(creator=l10n_bot, is_approved=False).annotate(locale=F("document__locale"))

    no_longer_needed = (
        Q(
            document__current_revision__based_on_id__gte=F(
                "document__parent__latest_localizable_revision_id"
            )
        )
        | Q(document__parent__is_archived=True)
        | Q(document__parent__html__startswith=REDIRECT_HTML)
    )

    # First, mark as reviewed any irrelevant machine translations that were awaiting review.
    for rev in qs.filter(
        reviewed__isnull=True,
    ).filter(
        # This machine translation is either out-of-date or no longer needed.
        Q(based_on_id__lt=F("document__parent__latest_localizable_revision_id"))
        | no_longer_needed
    ):
        rev.is_approved = False
        rev.reviewer = l10n_bot
        rev.reviewed = datetime.now()
        rev.comment = "No longer relevant."
        rev.save()
        # Record the action.
        RevisionActivityRecord.objects.create(
            revision=rev, action=RevisionActivityRecord.MT_REJECTED
        )
        add_to_report(rev.locale, "rejections", rev)

    # Next, publish pending machine translations, which are still-relevant machine
    # translations that have either not been reviewed and approved within the review
    # grace period, or were reviewed and not approved but an alternate translation
    # was not approved within the post-review grace period. We can't do an SQL update
    # because we need to trigger the Revision.save method.
    for rev in (
        qs.filter(
            based_on_id__gte=F("document__parent__latest_localizable_revision_id"),
        )
        .exclude(no_longer_needed)
        .filter(
            (Q(reviewed__isnull=True) & Q(created__lt=Now() - review_grace_period))
            | (
                Q(reviewed__isnull=False)
                & ~Q(reviewer=l10n_bot)
                & Q(reviewed__lt=Now() - post_review_grace_period)
            )
        )
    ):
        if rev.reviewed is None:
            rev.is_approved = True
            rev.reviewed = datetime.now()
            rev.reviewer = l10n_bot
            rev.comment = (
                "Automatically approved because it was not reviewed "
                f"within {duration_to_text(review_grace_period)}."
            )
            rev.save()
            # Record the action.
            RevisionActivityRecord.objects.create(
                revision=rev, action=RevisionActivityRecord.MT_APPROVED_PRE_REVIEW
            )
            add_to_report(rev.locale, "pre_review_approvals", rev)
        else:
            now = datetime.now()
            copy = Revision.objects.create(
                created=now,
                reviewed=now,
                is_approved=True,
                creator=l10n_bot,
                reviewer=l10n_bot,
                document_id=rev.document_id,
                based_on_id=rev.based_on_id,
                summary=rev.summary,
                content=rev.content,
                keywords=rev.keywords,
                comment=(
                    "Automatically created and approved because an alternate translation "
                    f"was not approved within {duration_to_text(post_review_grace_period)} "
                    f"after the rejection of {rev.get_absolute_url()}."
                ),
            )
            # Record the action.
            RevisionActivityRecord.objects.create(
                revision=copy, action=RevisionActivityRecord.MT_CREATED_AS_APPROVED_POST_REJECTION
            )
            add_to_report(rev.locale, "post_rejection_approvals", copy)

    return report
