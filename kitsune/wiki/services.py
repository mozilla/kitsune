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
from kitsune.wiki.strategies import TranslationRequest, TranslationStrategyFactory


class StaleTranslationService:
    """Service for managing stale translation detection and processing."""

    def __init__(self):
        self.strategy_factory = TranslationStrategyFactory()

    def find_stale_translation_candidates(
        self, target_locales: list[str] | None = None, limit: int | None = None
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
        sumo_bot = Profile.get_sumo_bot()

        # Skip translations that already have a pending LLM revision
        pending_sumo_bot_revision = Revision.objects.filter(
            document=OuterRef("pk"),
            creator=sumo_bot,
            is_approved=False,
            reviewed__isnull=True,
            based_on_id=OuterRef("parent__latest_localizable_revision_id"),
        )

        stale_translations = (
            Document.objects.filter(
                parent__isnull=False,  # Is a translation
                parent__is_localizable=True,
                parent__latest_localizable_revision__isnull=False,
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

    def process_stale_translations(
        self, limit: int | None = None, target_locales: list[str] | None = None
    ) -> list[tuple[Document, Document, str]]:
        """Process stale translations using appropriate strategies.

        Args:
            limit: Maximum number of translations to process
        Returns:
            List of tuples (english_document, translation_document, target_locale) that were processed
        """
        if limit is None:
            limit = settings.STALE_TRANSLATION_BATCH_SIZE

        candidates = self.find_stale_translation_candidates(
            limit=limit, target_locales=target_locales
        )

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
                    "previous_translation_revision_id": translation_doc.current_revision.id
                    if translation_doc.current_revision
                    else None,
                    "english_revision_date": english_doc.latest_localizable_revision.created.isoformat(),
                    "translation_revision_date": translation_doc.current_revision.created.isoformat()
                    if translation_doc.current_revision
                    else None,
                },
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
        translations_discontinued = Q(document__parent__is_archived=True) | Q(
            document__parent__html__startswith=REDIRECT_HTML
        )

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
