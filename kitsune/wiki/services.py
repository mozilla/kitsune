import logging
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

    def get_pending_sumobot_revisions(self) -> models.QuerySet[Revision]:
        """Build subquery for pending sumo bot revisions.

        Returns:
            Subquery that checks for unreviewed sumo bot revisions
        """
        return Revision.objects.filter(
            document=OuterRef("pk"),
            creator=self.sumo_bot,
            is_approved=False,
            reviewed__isnull=True,
            based_on_id=OuterRef("parent__latest_localizable_revision_id"),
        )

    def _base_english_docs(self) -> models.QuerySet[Document]:
        """Get base queryset for localizable English documents.

        Returns:
            QuerySet of English documents that can be translated
        """
        return (
            Document.objects.filter(
                locale=settings.WIKI_DEFAULT_LANGUAGE,
                is_localizable=True,
                latest_localizable_revision__isnull=False,
            )
            .exclude(html__startswith=REDIRECT_HTML)
        )

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
        pending_sumobot_revision = self.get_pending_sumobot_revisions()

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
            .annotate(has_pending_llm_revision=Exists(pending_sumobot_revision))
            .filter(has_pending_llm_revision=False)
        )

    def get_stale_docs_hybrid(self, limit: int | None = None) -> list[tuple[Document, Document, str]]:
        """Find non-archived stale translations in HYBRID locales.

        Distributes evenly across locales to avoid overloading reviewers.

        Args:
            limit: Maximum number of candidates to return

        Returns:
            List of tuples: (english_document, translation_document, target_locale)
        """
        if limit is None:
            limit = settings.STALE_TRANSLATION_BATCH_SIZE

        cutoff_date = timezone.now() - timedelta(days=settings.STALE_TRANSLATION_THRESHOLD_DAYS)
        result: list[tuple[Document, Document, str]] = []

        for locale in settings.HYBRID_ENABLED_LOCALES:
            if len(result) >= limit:
                break

            remaining = limit - len(result)
            fetch_count = min(settings.HYBRID_QUOTA_PER_LOCALE, remaining)

            queryset = (
                self._base_stale_translations([locale], cutoff_date)
                .filter(parent__is_archived=False)[:fetch_count]
            )

            result.extend(
                (translation_doc.parent, translation_doc, translation_doc.locale)
                for translation_doc in queryset
            )

        return result

    def get_stale_docs_ai(self, limit: int | None = None) -> list[tuple[Document, Document, str]]:
        """Find stale translations for AI flow.

        Includes:
        - All documents (archived + non-archived) in AI locales
        - Only archived documents in HYBRID locales

        Args:
            limit: Maximum number of candidates to return

        Returns:
            List of tuples: (english_document, translation_document, target_locale)
        """
        cutoff_date = timezone.now() - timedelta(days=settings.STALE_TRANSLATION_THRESHOLD_DAYS)

        # AI locales: all documents
        ai_locales_queryset = self._base_stale_translations(settings.AI_ENABLED_LOCALES, cutoff_date)

        # HYBRID locales: only archived documents
        hybrid_locales_queryset = (
            self._base_stale_translations(settings.HYBRID_ENABLED_LOCALES, cutoff_date)
            .filter(parent__is_archived=True)
        )

        # Combine both querysets
        queryset = ai_locales_queryset.union(hybrid_locales_queryset)

        if limit:
            queryset = queryset[:limit]

        return [
            (translation_doc.parent, translation_doc, translation_doc.locale)
            for translation_doc in queryset
        ]

    def get_missing_docs_hybrid(self, limit: int | None = None) -> list[tuple[Document, None, str]]:
        """Find non-archived English docs without translations in HYBRID locales.

        Distributes evenly across locales to avoid overloading reviewers.

        Args:
            limit: Maximum number of candidates to return

        Returns:
            List of tuples: (english_document, None, target_locale)
        """
        if limit is None:
            limit = settings.STALE_TRANSLATION_BATCH_SIZE

        result: list[tuple[Document, None, str]] = []

        for locale in settings.HYBRID_ENABLED_LOCALES:
            if len(result) >= limit:
                break

            remaining = limit - len(result)
            fetch_count = min(settings.HYBRID_QUOTA_PER_LOCALE, remaining)

            docs = (
                self._base_english_docs()
                .filter(is_archived=False)
                .exclude(translations__locale=locale)
                .select_related("latest_localizable_revision")
                .order_by("-latest_localizable_revision__created")[:fetch_count]
            )

            result.extend((doc, None, locale) for doc in docs)

        return result

    def get_missing_docs_ai(self, limit: int | None = None) -> list[tuple[Document, None, str]]:
        """Find English docs without translations for AI flow.

        Includes:
        - All documents (archived + non-archived) in AI locales
        - Only archived documents in HYBRID locales

        Args:
            limit: Maximum number of candidates to return

        Returns:
            List of tuples: (english_document, None, target_locale)
        """
        # Combine AI and HYBRID locales
        all_locales = list(settings.AI_ENABLED_LOCALES) + list(settings.HYBRID_ENABLED_LOCALES)
        missing_translations: list[tuple[Document, None, str]] = []

        for locale in all_locales:
            if limit is not None and len(missing_translations) >= limit:
                break

            # Build archive filter based on locale type
            base_query = self._base_english_docs().exclude(translations__locale=locale)

            if locale in settings.AI_ENABLED_LOCALES:
                # AI locales: all documents
                docs = base_query
            else:
                # HYBRID locales: only archived documents
                docs = base_query.filter(is_archived=True)

            docs = (
                docs
                .select_related("latest_localizable_revision")
                .order_by("-latest_localizable_revision__created")
            )

            remaining_limit = limit - len(missing_translations) if limit else None
            if remaining_limit:
                docs = docs[:remaining_limit]

            missing_translations.extend((doc, None, locale) for doc in docs)

        return missing_translations

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
            created__lt=Now() - timedelta(hours=settings.HYBRID_REVIEW_GRACE_PERIOD),
        ).exclude(another_already_approved | translations_discontinued)

    def get_obsolete_translations(self, document: Document | None = None) -> models.QuerySet[Revision]:
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
            translation_method = self.strategy_factory.get_method_for_document(
                english_doc, locale
            )

            metadata = {"english_revision_date": english_doc.latest_localizable_revision.created.isoformat()}

            if translation_doc:
                metadata.update({
                    "stale_translation_update": True,
                    "previous_translation_revision_id": translation_doc.current_revision.id
                    if translation_doc.current_revision
                    else None,
                    "translation_revision_date": translation_doc.current_revision.created.isoformat()
                    if translation_doc.current_revision
                    else None,
                })

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

    def process_stale(
        self, limit: int | None = None, strategy: str | None = None
    ) -> list[tuple[Document, Document | None, str]]:
        """Process stale translations using appropriate strategies.

        Args:
            limit: Maximum number of translations to process
            strategy: Optional strategy filter (TranslationMethod.AI or TranslationMethod.HYBRID)
        Returns:
            List of tuples (english_document, translation_document, target_locale) that were processed
        """
        if limit is None:
            limit = settings.STALE_TRANSLATION_BATCH_SIZE

        if strategy == TranslationMethod.AI:
            candidates = self.query_builder.get_stale_docs_ai(limit)
        elif strategy == TranslationMethod.HYBRID:
            candidates = self.query_builder.get_stale_docs_hybrid(limit)
        else:
            ai_candidates = self.query_builder.get_stale_docs_ai(limit)
            hybrid_limit = limit - len(ai_candidates) if limit else None
            hybrid_candidates = self.query_builder.get_stale_docs_hybrid(hybrid_limit)
            candidates = ai_candidates + hybrid_candidates

        return super().process(candidates, TranslationTrigger.STALE_TRANSLATION_UPDATE)


class MissingTranslationService(BaseTranslationService):
    """Service for managing missing translation detection and processing."""

    def process_missing(
        self, limit: int | None = None, strategy: str | None = None
    ) -> list[tuple[Document, Document | None, str]]:
        """Process missing translations using appropriate strategies.

        Args:
            limit: Maximum number of translations to process
            strategy: Optional strategy filter (TranslationMethod.AI or TranslationMethod.HYBRID)
        Returns:
            List of tuples (english_document, None, target_locale) that were processed
        """
        if limit is None:
            limit = settings.STALE_TRANSLATION_BATCH_SIZE

        if strategy == TranslationMethod.AI:
            candidates = self.query_builder.get_missing_docs_ai(limit)
        elif strategy == TranslationMethod.HYBRID:
            candidates = self.query_builder.get_missing_docs_hybrid(limit)
        else:
            ai_candidates = self.query_builder.get_missing_docs_ai(limit)
            hybrid_limit = limit - len(ai_candidates) if limit else None
            hybrid_candidates = self.query_builder.get_missing_docs_hybrid(hybrid_limit)
            candidates = ai_candidates + hybrid_candidates

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
        if not (settings.HYBRID_REVIEW_GRACE_PERIOD and settings.HYBRID_ENABLED_LOCALES):
            return

        grace_period = f"{settings.HYBRID_REVIEW_GRACE_PERIOD} hour(s)"
        pending_revisions = self.query_builder.get_pending_translations()

        for revision in pending_revisions:
            rev = self.content_manager.publish_revision(
                revision,
                comment=(
                    f"Automatically approved because it was not reviewed within {grace_period}."
                ),
            )
            if log:
                log.info(
                    f"Automatically approved {rev.get_absolute_url()} because it was not"
                    f" reviewed within {grace_period}."
                )
