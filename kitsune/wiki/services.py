from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from kitsune.wiki.models import Document
from kitsune.wiki.strategies import TranslationRequest, TranslationStrategyFactory


class StaleTranslationService:
    """Service for managing stale translation detection and processing."""

    def __init__(self):
        self.strategy_factory = TranslationStrategyFactory()

    def find_stale_translation_candidates(
        self,
        target_locales: list[str] | None = None,
        limit: int | None = None
    ) -> list[tuple[Document, Document, str]]:
        """Find English articles with stale translations that need updating.

        Args:
            target_locales: List of locales to check (defaults to AI+HYBRID enabled locales)
            limit: Maximum number of candidates to return
        Returns:
            List of tuples: (english_document, translation_document, target_locale)
        """
        if target_locales is None:
            target_locales = settings.AI_ENABLED_LOCALES + settings.HYBRID_ENABLED_LOCALES

        cutoff_date = timezone.now() - timedelta(days=settings.STALE_TRANSLATION_THRESHOLD_DAYS)

        stale_translations = Document.objects.filter(
            parent__isnull=False,  # Is a translation
            parent__is_localizable=True,
            parent__latest_localizable_revision__isnull=False,
            current_revision__created__lt=cutoff_date,
            locale__in=target_locales,
            current_revision__isnull=False
        ).select_related(
            'parent',
            'parent__latest_localizable_revision',
            'current_revision'
        ).filter(
            # Parent has been updated since this translation
            parent__latest_localizable_revision__created__gt=models.F('current_revision__created')
        )

        if limit is not None:
            stale_translations = stale_translations[:limit]

        candidates = [
            (translation_doc.parent, translation_doc, translation_doc.locale)
            for translation_doc in stale_translations
        ]
        return candidates

    def process_stale_translations(self, limit: int | None = None) -> list[tuple[Document, Document, str]]:
        """Process stale translations using appropriate strategies.

        Args:
            limit: Maximum number of translations to process
        Returns:
            List of tuples (english_document, translation_document, target_locale) that were processed
        """
        if limit is None:
            limit = settings.STALE_TRANSLATION_BATCH_SIZE

        candidates = self.find_stale_translation_candidates(limit=limit)

        for english_doc, translation_doc, locale in candidates:
            translation_method = self.strategy_factory.get_method_for_locale(locale)

            l10n_request = TranslationRequest(
                revision=english_doc.latest_localizable_revision,
                trigger="stale_translation_update",
                target_locale=locale,
                method=translation_method,
                asynchronous=True,
                metadata={
                    "stale_translation_update": True,
                    "previous_translation_revision_id": translation_doc.current_revision.id if translation_doc.current_revision else None,
                    "english_revision_date": english_doc.latest_localizable_revision.created.isoformat(),
                    "translation_revision_date": translation_doc.current_revision.created.isoformat() if translation_doc.current_revision else None
                }
            )
            self.strategy_factory.execute(l10n_request)
        return candidates
