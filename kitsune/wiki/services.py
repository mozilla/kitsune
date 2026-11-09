import logging
import random
from collections.abc import Callable
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Exists, F, OuterRef, Q
from django.db.models.functions import Now
from django.utils import timezone

from kitsune.users.models import Profile
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.wiki.content_managers import HybridContentManager
from kitsune.wiki.models import Document, Revision
from kitsune.wiki.strategies import (
    TranslationMethod,
    TranslationRequest,
    TranslationStrategyFactory,
    TranslationTrigger,
)


class TranslationQueryBuilder:
    """Provides queries for finding translation candidates across different strategies."""

    def __init__(self):
        self.sumo_bot = Profile.get_sumo_bot()

    def get_pending_revisions(self) -> models.QuerySet[Revision]:
        """Build subquery for pending revisions that make a new translation unnecessary.

        A revision qualifies when it's awaiting review, covers the latest localizable
        English revision or newer, and either we created it or someone else created it
        recently enough that it may still be reviewed within the grace period.

        Returns:
            Subquery that checks for unreviewed revisions
        """
        created_within_grace_period = Q(
            created__gte=Now() - timedelta(hours=settings.REVIEW_GRACE_PERIOD)
        )

        return Revision.objects.filter(
            document=OuterRef("pk"),
            is_approved=False,
            reviewed__isnull=True,
            based_on_id__gte=OuterRef("parent__latest_localizable_revision_id"),
        ).filter(Q(creator=self.sumo_bot) | created_within_grace_period)

    def _base_english_docs(self) -> models.QuerySet[Document]:
        """Get base queryset for localizable English documents.

        Returns:
            QuerySet of English documents that can be translated
        """
        return Document.objects.filter(
            locale=settings.WIKI_DEFAULT_LANGUAGE,
            is_localizable=True,
            latest_localizable_revision__isnull=False,
        ).exclude(html__startswith=REDIRECT_HTML)

    def _base_stale_translations(
        self, target_locales: list[str], cutoff_date
    ) -> models.QuerySet[Document]:
        """Build the base query for stale translations.

        Args:
            target_locales: List of locales to check
            cutoff_date: Datetime threshold for staleness

        Returns:
            QuerySet of translation documents that are stale
        """
        english_docs = self._base_english_docs()
        pending_revision = self.get_pending_revisions()

        return (
            Document.objects.filter(
                parent__in=english_docs,
                current_revision__created__lt=cutoff_date,
                locale__in=target_locales,
                current_revision__isnull=False,
            )
            .select_related("parent", "parent__latest_localizable_revision", "current_revision")
            .filter(
                parent__latest_localizable_revision__created__gt=models.F(
                    "current_revision__created"
                )
            )
            .annotate(has_pending_revision=Exists(pending_revision))
            .filter(has_pending_revision=False)
        )

    def _pick(
        self,
        method: TranslationMethod,
        candidates: Callable[[str, bool], models.QuerySet[Document]],
    ) -> list[tuple[str, int]]:
        """Pick documents for one flow, within its per-run budget.

        The budget is shared round-robin, one document per round to each locale that still has
        candidates, in a locale order shuffled on every run, so when the budget can't reach every
        locale the locales left out change from run to run. In the AI flow, non-archived documents
        in AI locales come first; archived documents in AI and HYBRID locales share what's left.
        In the HYBRID flow, no locale gets more than HYBRID_QUOTA_PER_LOCALE.

        Args:
            method: TranslationMethod.AI or TranslationMethod.HYBRID
            candidates: Builds the candidate queryset for a locale and an archive status

        Returns:
            List of tuples: (locale, document_id)
        """
        if method == TranslationMethod.AI:
            budget = per_locale = settings.AI_TRANSLATION_BATCH_SIZE
            tiers = [
                (settings.AI_ENABLED_LOCALES, False),
                ([*settings.AI_ENABLED_LOCALES, *settings.HYBRID_ENABLED_LOCALES], True),
            ]
        elif method == TranslationMethod.HYBRID:
            budget = settings.HYBRID_TRANSLATION_BATCH_SIZE
            per_locale = settings.HYBRID_QUOTA_PER_LOCALE
            tiers = [(settings.HYBRID_ENABLED_LOCALES, False)]
        else:
            raise ValueError(f"No translation budget for {method!r}")

        picks: list[tuple[str, int]] = []
        for locales, is_archived in tiers:
            left = budget - len(picks)
            fetch = min(left, per_locale)
            if fetch <= 0:
                break

            pool: dict[str, list[int]] = {}
            for locale in dict.fromkeys(locales):
                queryset = candidates(locale, is_archived).values_list("id", flat=True)
                if ids := list(queryset[:fetch]):
                    pool[locale] = ids

            order = list(pool)
            random.shuffle(order)
            taken = dict.fromkeys(order, 0)
            while left > 0 and order:
                for locale in order[:left]:
                    taken[locale] += 1
                left -= min(left, len(order))
                order = [locale for locale in order if taken[locale] < len(pool[locale])]

            picks += [
                (locale, pk) for locale, count in taken.items() for pk in pool[locale][:count]
            ]
        return picks

    def get_stale_docs(self, method: TranslationMethod) -> list[tuple[Document, Document, str]]:
        """Find stale translations for one flow, within its per-run budget (see `_pick`).

        Returns:
            List of tuples: (english_document, translation_document, target_locale)
        """
        cutoff_date = timezone.now() - timedelta(days=settings.STALE_TRANSLATION_THRESHOLD_DAYS)
        picks = self._pick(
            method,
            lambda locale, is_archived: self._base_stale_translations(
                [locale], cutoff_date
            ).filter(parent__is_archived=is_archived),
        )
        docs = Document.objects.select_related(
            "parent", "parent__latest_localizable_revision", "current_revision"
        ).in_bulk([pk for _, pk in picks])
        return [(docs[pk].parent, docs[pk], locale) for locale, pk in picks if pk in docs]

    def get_missing_docs(self, method: TranslationMethod) -> list[tuple[Document, None, str]]:
        """Find untranslated English documents for one flow, within its per-run budget.

        Each locale takes the newest English revisions first (see `_pick` for the spread).

        Returns:
            List of tuples: (english_document, None, target_locale)
        """
        picks = self._pick(
            method,
            lambda locale, is_archived: (
                self._base_english_docs()
                .filter(is_archived=is_archived)
                .exclude(translations__locale=locale)
                .order_by("-latest_localizable_revision__created")
            ),
        )
        docs = Document.objects.select_related("latest_localizable_revision").in_bulk(
            {pk for _, pk in picks}
        )
        return [(docs[pk], None, locale) for locale, pk in picks if pk in docs]

    def get_pending_translations(self) -> models.QuerySet[Revision]:
        """Find unreviewed hybrid translations pending grace period expiration.

        Returns:
            QuerySet of Revision objects that need auto-approval
        """
        english_docs = self._base_english_docs().filter(is_archived=False)

        unreviewed_translations = Revision.objects.filter(
            creator=self.sumo_bot,
            is_approved=False,
            reviewed__isnull=True,
            schedule__isnull=True,
            document__parent__in=english_docs,
            document__locale__in=settings.HYBRID_ENABLED_LOCALES,
        )

        another_already_approved = Q(
            document__current_revision__based_on_id__gte=F(
                "document__parent__latest_localizable_revision_id"
            )
        )
        translations_discontinued = Q(document__parent__html__startswith=REDIRECT_HTML)

        return unreviewed_translations.filter(
            based_on_id__gte=F("document__parent__latest_localizable_revision_id"),
            created__lt=Now() - timedelta(hours=settings.REVIEW_GRACE_PERIOD),
        ).exclude(another_already_approved | translations_discontinued)

    def get_obsolete_translations(
        self, document: Document | None = None
    ) -> models.QuerySet[Revision]:
        """Find unreviewed hybrid translations that are no longer useful.

        Args:
            document: Optional document to filter by. If provided, returns obsolete
                     translations for that specific document (either as parent or translation).
                     If None, returns all obsolete translations.

        Returns:
            QuerySet of Revision objects that should be rejected
        """
        english_docs = self._base_english_docs().filter(is_archived=False)

        unreviewed_translations = Revision.objects.filter(
            creator=self.sumo_bot,
            is_approved=False,
            reviewed__isnull=True,
            document__parent__in=english_docs,
            document__locale__in=settings.HYBRID_ENABLED_LOCALES,
        )

        outdated = Q(based_on_id__lt=F("document__parent__latest_localizable_revision_id"))
        another_already_approved = Q(
            document__current_revision__based_on_id__gte=F(
                "document__parent__latest_localizable_revision_id"
            )
        )
        translations_discontinued = Q(document__parent__html__startswith=REDIRECT_HTML)

        queryset = unreviewed_translations.filter(
            outdated | another_already_approved | translations_discontinued
        )

        if document is not None:
            if document.locale == settings.WIKI_DEFAULT_LANGUAGE:
                queryset = queryset.filter(document__parent=document)
            elif document.locale in settings.HYBRID_ENABLED_LOCALES:
                queryset = queryset.filter(document=document)
            else:
                return Revision.objects.none()

        return queryset


class BaseTranslationService:
    """Base service for managing translation processing."""

    def __init__(self):
        self.strategy_factory = TranslationStrategyFactory()
        self.query_builder = TranslationQueryBuilder()

    def process(
        self,
        candidates: list[tuple[Document, Document | None, str]],
        trigger: TranslationTrigger,
    ) -> list[tuple[Document, Document | None, str]]:
        """Process translation candidates using appropriate strategies.

        Args:
            candidates: List of tuples (english_doc, translation_doc, locale)
            trigger: The trigger type for this translation
        Returns:
            The list of processed candidates
        """
        for english_doc, translation_doc, locale in candidates:
            translation_method = self.strategy_factory.get_method_for_document(english_doc, locale)

            metadata = {
                "english_revision_date": english_doc.latest_localizable_revision.created.isoformat()
            }

            if translation_doc:
                metadata.update(
                    {
                        "stale_translation_update": True,
                        "previous_translation_revision_id": translation_doc.current_revision.id
                        if translation_doc.current_revision
                        else None,
                        "translation_revision_date": translation_doc.current_revision.created.isoformat()
                        if translation_doc.current_revision
                        else None,
                    }
                )

            l10n_request = TranslationRequest(
                revision=english_doc.latest_localizable_revision,
                trigger=trigger,
                target_locale=locale,
                method=translation_method,
                asynchronous=True,
                metadata=metadata,
            )
            self.strategy_factory.execute(l10n_request)
        return candidates


class StaleTranslationService(BaseTranslationService):
    """Service for managing stale translation detection and processing."""

    def process_stale(self) -> list[tuple[Document, Document | None, str]]:
        """Process stale translations, each flow within its own per-run budget.

        Returns:
            List of tuples (english_document, translation_document, target_locale) that were processed
        """
        candidates = [
            *self.query_builder.get_stale_docs(TranslationMethod.AI),
            *self.query_builder.get_stale_docs(TranslationMethod.HYBRID),
        ]
        return super().process(candidates, TranslationTrigger.STALE_TRANSLATION_UPDATE)


class MissingTranslationService(BaseTranslationService):
    """Service for managing missing translation detection and processing."""

    def process_missing(self) -> list[tuple[Document, Document | None, str]]:
        """Process missing translations, each flow within its own per-run budget.

        Returns:
            List of tuples (english_document, None, target_locale) that were processed
        """
        candidates = [
            *self.query_builder.get_missing_docs(TranslationMethod.AI),
            *self.query_builder.get_missing_docs(TranslationMethod.HYBRID),
        ]
        return super().process(candidates, TranslationTrigger.INITIAL_TRANSLATION)


class HybridTranslationService:
    def __init__(self):
        self.content_manager = HybridContentManager()
        self.query_builder = TranslationQueryBuilder()

    def reject_obsolete_translations(self, document: Document) -> None:
        """Reject obsolete machine translations for the given document."""
        if not settings.HYBRID_ENABLED_LOCALES:
            return

        obsolete_revisions = self.query_builder.get_obsolete_translations(document)

        for rev in obsolete_revisions:
            self.content_manager.reject_revision(rev, comment="No longer relevant.")

    def publish_pending_translations(self, log: logging.Logger | None = None) -> None:
        """Publish fresh machine translations that have not been reviewed within the grace period."""
        if not (settings.REVIEW_GRACE_PERIOD and settings.HYBRID_ENABLED_LOCALES):
            return

        grace_period = settings.REVIEW_GRACE_PERIOD
        if grace_period <= 72:
            grace_period_string = f"{grace_period} hour{'s' if grace_period > 1 else ''}"
        else:
            grace_period = grace_period // 24
            grace_period_string = f"{grace_period} day{'s' if grace_period > 1 else ''}"

        pending_revisions = self.query_builder.get_pending_translations()
        for revision in pending_revisions:
            rev = self.content_manager.publish_revision(
                revision,
                comment=(
                    f"Automatically approved because it was not reviewed within {grace_period_string}."
                ),
            )
            if log:
                log.info(
                    f"Automatically approved {rev.get_absolute_url()} because it was not"
                    f" reviewed within {grace_period_string}."
                )
