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
    TranslationRequest,
    TranslationStrategyFactory,
    TranslationTrigger,
)


class TranslationService:
    """Service for managing automatic translation detection and processing."""

    def __init__(self):
        self.strategy_factory = TranslationStrategyFactory()
        self.sumo_bot = Profile.get_sumo_bot()

    def _get_target_locales(self, target_locales: list[str] | None) -> list[str]:
        """Get target locales, defaulting to AI+HYBRID enabled locales."""
        if target_locales is None:
            return settings.AI_ENABLED_LOCALES + settings.HYBRID_ENABLED_LOCALES
        return target_locales

    def _get_base_english_docs_query(self):
        """Get base queryset for localizable English documents."""
        return Document.objects.filter(
            locale=settings.WIKI_DEFAULT_LANGUAGE,
            is_localizable=True,
            latest_localizable_revision__isnull=False,
        ).exclude(html__startswith=REDIRECT_HTML)

    def get_stale_translations(
        self, target_locales: list[str] | None = None, limit: int | None = None
    ) -> list[tuple[Document, Document | None, str]]:
        """Find English articles with stale translations that need updating.

        Args:
            target_locales: List of locales to check (defaults to AI+HYBRID enabled locales)
            limit: Maximum number of candidates to return
        Returns:
            List of tuples: (english_document, translation_document, target_locale)
        """
        target_locales = self._get_target_locales(target_locales)

        cutoff_date = timezone.now() - timedelta(days=settings.STALE_TRANSLATION_THRESHOLD_DAYS)

        # Get base English documents query
        english_docs = self._get_base_english_docs_query()

        # Skip translations that already have a pending LLM revision
        pending_sumo_bot_revision = Revision.objects.filter(
            document=OuterRef("pk"),
            creator=self.sumo_bot,
            is_approved=False,
            reviewed__isnull=True,
            based_on_id=OuterRef("parent__latest_localizable_revision_id"),
        )

        stale_translations = (
            Document.objects.filter(
                parent__in=english_docs,
                current_revision__created__lt=cutoff_date,
                locale__in=target_locales,
                current_revision__isnull=False,
            )
            .select_related("parent", "parent__latest_localizable_revision", "current_revision")
            .filter(
                # Parent has been updated since this translation
                parent__latest_localizable_revision__created__gt=models.F(
                    "current_revision__created"
                )
            )
            .annotate(has_pending_llm_revision=Exists(pending_sumo_bot_revision))
            .filter(has_pending_llm_revision=False)
        )

        if limit is not None:
            stale_translations = stale_translations[:limit]

        candidates = [
            (translation_doc.parent, translation_doc, translation_doc.locale)
            for translation_doc in stale_translations
        ]
        return candidates

    def get_missing_translations(
        self, target_locales: list[str] | None = None, limit: int | None = None
    ) -> list[tuple[Document, Document | None, str]]:
        """Find English articles that are missing translations in enabled locales.

        Args:
            target_locales: List of locales to check (defaults to AI+HYBRID enabled locales)
            limit: Maximum number of missing translations to return
        Returns:
            List of tuples: (english_document, None, target_locale)
        """
        target_locales = self._get_target_locales(target_locales)

        missing_translations: list[tuple[Document, Document | None, str]] = []

        for locale in target_locales:
            if limit is not None and len(missing_translations) >= limit:
                break

            # Find English docs that don't have a translation in this locale
            docs = (
                self._get_base_english_docs_query()
                .exclude(translations__locale=locale)
                .select_related("latest_localizable_revision")
                .order_by("-latest_localizable_revision__created")
            )

            # Apply remaining limit
            remaining_limit = limit - len(missing_translations) if limit else None
            if remaining_limit:
                docs = docs[:remaining_limit]

            for doc in docs:
                missing_translations.append((doc, None, locale))
                if limit and len(missing_translations) >= limit:
                    break

        return missing_translations

    def process_translations(
        self,
        limit: int | None = None,
        target_locales: list[str] | None = None,
        create: bool = False,
    ) -> list[tuple[Document, Document | None, str]]:
        """Process translations using appropriate strategies.

        Args:
            limit: Maximum number of translations to process
            target_locales: List of locales to check (defaults to AI+HYBRID enabled locales)
            create: If True, create missing translations; if False, update stale translations
        Returns:
            List of tuples (english_document, translation_document, target_locale) that were processed
        """
        if limit is None:
            limit = settings.STALE_TRANSLATION_BATCH_SIZE

        candidates: list[tuple[Document, Document | None, str]]
        if create:
            candidates = self.get_missing_translations(limit=limit, target_locales=target_locales)
            trigger = TranslationTrigger.INITIAL_TRANSLATION
            metadata_key = "initial_translation"
        else:
            candidates = self.get_stale_translations(limit=limit, target_locales=target_locales)
            trigger = TranslationTrigger.STALE_TRANSLATION_UPDATE
            metadata_key = "stale_translation_update"

        for english_doc, translation_doc, locale in candidates:
            translation_method = self.strategy_factory.get_method_for_locale(locale)

            metadata = {
                metadata_key: True,
                "english_revision_date": english_doc.latest_localizable_revision.created.isoformat(),
            }

            if translation_doc and translation_doc.current_revision:
                metadata.update(
                    {
                        "previous_translation_revision_id": translation_doc.current_revision.id,
                        "translation_revision_date": translation_doc.current_revision.created.isoformat(),
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


class HybridTranslationService:
    def __init__(self):
        self.content_manager = HybridContentManager()

        # Define the queries that will be needed only once.

        sumo_bot = Profile.get_sumo_bot()

        unreviewed_translations = Revision.objects.filter(
            creator=sumo_bot,
            is_approved=False,
            reviewed__isnull=True,
            document__parent__is_localizable=True,
            document__parent__current_revision__isnull=False,
            document__parent__latest_localizable_revision__isnull=False,
            document__locale__in=settings.HYBRID_ENABLED_LOCALES,
        )

        outdated = Q(based_on_id__lt=F("document__parent__latest_localizable_revision_id"))
        another_already_approved = Q(
            document__current_revision__based_on_id__gte=F(
                "document__parent__latest_localizable_revision_id"
            )
        )
        translations_discontinued = Q(document__parent__html__startswith=REDIRECT_HTML)

        # Unreviewed machine translations that are no longer useful.
        self._qs_obsolete = unreviewed_translations.filter(
            outdated | another_already_approved | translations_discontinued
        )

        # Fresh, unreviewed machine translations that have not been reviewed within
        # the grace period.
        self._qs_pending = unreviewed_translations.filter(
            based_on_id__gte=F("document__parent__latest_localizable_revision_id"),
            created__lt=Now() - timedelta(hours=settings.HYBRID_REVIEW_GRACE_PERIOD),
        ).exclude(another_already_approved | translations_discontinued)

    def reject_obsolete_translations(self, document: Document) -> None:
        """
        Reject obsolete machine translations for the given document.
        """
        if not settings.HYBRID_ENABLED_LOCALES:
            return

        if document.locale == settings.WIKI_DEFAULT_LANGUAGE:
            qs_obsolete = self._qs_obsolete.filter(document__parent=document)
        elif document.locale in settings.HYBRID_ENABLED_LOCALES:
            qs_obsolete = self._qs_obsolete.filter(document=document)
        else:
            return

        for rev in qs_obsolete:
            self.content_manager.reject_revision(rev, comment="No longer relevant.")

    def publish_pending_translations(self, log: logging.Logger | None = None) -> None:
        """
        Publish fresh machine translations that have not been reviewed within the grace period.
        """
        if not (settings.HYBRID_REVIEW_GRACE_PERIOD and settings.HYBRID_ENABLED_LOCALES):
            return

        grace_period = f"{settings.HYBRID_REVIEW_GRACE_PERIOD} hour(s)"

        for revision in self._qs_pending:
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
