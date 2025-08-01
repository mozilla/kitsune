from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from kitsune.wiki.config import TYPO_SIGNIFICANCE
from kitsune.wiki.models import DraftRevision, Revision


class TranslationMethod(models.TextChoices):
    """Available translation methods."""
    AI = "ai", "AI Translation"
    MANUAL = "manual", "Manual Translation"
    HYBRID = "hybrid", "Hybrid Translation"
    VENDOR = "vendor", "Vendor Translation"


@dataclass
class TranslationRequest:
    revision: Revision
    trigger: str
    user: User | None = None
    target_locale: str | None = None
    method: Any = TranslationMethod.MANUAL
    priority: str = "normal"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationResult:
    """Result of translation operation."""
    success: bool
    method: Any = None
    translated_content: str | None = None
    error_message: str | None = None
    cost: float = 0.0
    quality_score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AbstractTranslationStrategy(ABC):
    """Abstract base class for translation strategies."""

    @abstractmethod
    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform translation using this strategy."""
        pass

    @abstractmethod
    def can_handle(self, l10n_request: TranslationRequest) -> bool:
        """Check if this strategy can handle the request (basic validation)."""
        pass


class TranslationStrategy(AbstractTranslationStrategy):
    """Base class for translation strategies."""

    def _is_localizable_document(self, revision: Revision) -> bool:
        """Check if a document is localizable."""
        try:
            document = revision.document
        except revision.__class__.document.RelatedObjectDoesNotExist:
            # Document doesn't exist or isn't loaded
            return False

        return all([
            document.is_localizable,
            document.locale == settings.WIKI_DEFAULT_LANGUAGE,
            revision.is_approved,
            not revision.significance or revision.significance > TYPO_SIGNIFICANCE
        ])

    def can_handle(self, l10n_request: TranslationRequest) -> bool:
        """Check if this strategy can handle the request (basic validation)."""
        revision = l10n_request.revision
        return self._is_localizable_document(revision)


    @classmethod
    def can_handle_revision(cls, revision: Revision) -> bool:
        """Check if a revision meets basic criteria for l10n."""
        return cls()._is_localizable_document(revision)

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform translation using this strategy."""
        return TranslationResult(
            success=True,
            method=TranslationMethod.MANUAL,
            metadata={}
        )


class AITranslationStrategy(TranslationStrategy):
    """AI-based translation strategy without human review."""

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform AI translation."""
        # placeholder for AI translation logic

        return TranslationResult(
            success=True,
            method=TranslationMethod.AI,
            translated_content="",
            cost=0.0,
            quality_score=1.0,
            metadata={}
        )


class HybridTranslationStrategy(TranslationStrategy):
    """Hybrid translation strategy (AI + Human review)."""

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform hybrid translation."""

        # placeholder for hybrid translation logic
        return TranslationResult(
            success=True,
            method=TranslationMethod.HYBRID,
            translated_content='',
            cost=0.0,
            quality_score=0.95,
            metadata={}
        )


class ManualTranslationStrategy(TranslationStrategy):
    """Manual translation workflow coordinator."""

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Execute manual translation strategy based on trigger."""
        if not self.can_handle(l10n_request):
            return TranslationResult(
                success=False,
                method=TranslationMethod.MANUAL,
                error_message="Revision cannot be marked as ready for localization"
            )

        revision = l10n_request.revision
        message = None

        match l10n_request.trigger:
            case "mark_ready_for_l10n":
                if revision.is_ready_for_localization:
                    message = "Revision is already ready for localization"
                self._handle_mark_ready_for_l10n(l10n_request)
            case "review_revision":
                if not revision.is_ready_for_localization:
                    message = "Revision is not ready for localization"
                return self._handle_review_revision(l10n_request)
            case _:
                message = f"Unknown trigger: {l10n_request.trigger}"

        return TranslationResult(
            success=False,
            method=TranslationMethod.MANUAL,
            error_message=message
        )

    def _handle_mark_ready_for_l10n(self, l10n_request: TranslationRequest) -> None:
        """Handle mark_ready_for_l10n trigger - just update DB."""
        revision = l10n_request.revision
        user = l10n_request.user

        revision.is_ready_for_localization = True
        revision.readied_for_localization = datetime.now()
        revision.readied_for_localization_by = user
        revision.save()

    def _handle_review_revision(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Handle review_revision trigger - full workflow."""
        # Step 1: Update database (mark as ready for l10n)
        self._update_revision_for_localization(l10n_request)
        # Step 2: Fire notifications to translators
        self._notify_translators(l10n_request)
        # Step 3: Create translation tracking context
        translation_context = self._create_translation_context(l10n_request)
        # Step 4: Handle draft management
        draft_info = self._manage_drafts(l10n_request)
        # Step 5: Generate translation URLs
        translation_urls = self._generate_translation_urls(l10n_request)

        return TranslationResult(
            success=True,
            method=TranslationMethod.MANUAL,
            metadata={
                "translation_context": translation_context,
                "translation_urls": translation_urls,
                "draft_info": draft_info
            }
        )

    def _update_revision_for_localization(self, l10n_request: TranslationRequest) -> None:
        """Update revision to mark it as ready for localization."""
        revision = l10n_request.revision
        revision.is_ready_for_localization = True
        revision.readied_for_localization = datetime.now()
        revision.save()

    def _notify_translators(self, l10n_request: TranslationRequest) -> None:
        """Fire notifications to translators about the ready revision."""
        from kitsune.wiki.events import ApprovedOrReadyUnion
        ApprovedOrReadyUnion(l10n_request.revision).fire()

    def _create_translation_context(self, l10n_request: TranslationRequest) -> dict[str, Any]:
        """Create translation tracking context."""
        document = l10n_request.revision.document

        existing_translations = document.translations.all()
        translated_locales = list(existing_translations.values_list('locale', flat=True))

        all_locales = [locale[0] for locale in settings.LANGUAGE_CHOICES]
        untranslated_locales = [locale for locale in all_locales
                              if locale not in translated_locales and locale != document.locale]

        return {
            "document_id": document.id,
            "revision_id": l10n_request.revision.id,
            "source_locale": document.locale,
            "target_locale": l10n_request.target_locale,
            "existing_translations": translated_locales,
            "untranslated_locales": untranslated_locales,
            "translation_status": "pending",
            "created_at": l10n_request.revision.created.isoformat()
        }

    def _manage_drafts(self, l10n_request: TranslationRequest) -> dict[str, Any]:
        """Manage draft revisions for the translation."""
        document = l10n_request.revision.document
        target_locale = l10n_request.target_locale

        existing_drafts = DraftRevision.objects.filter(
            document=document,
            locale=target_locale
        )

        outdated_drafts = []
        for draft in existing_drafts:
            if draft.based_on and draft.based_on.id != l10n_request.revision.id:
                outdated_drafts.append({
                    "draft_id": draft.id,
                    "based_on_revision": draft.based_on.id,
                    "current_revision": l10n_request.revision.id,
                    "is_outdated": True
                })

        return {
            "drafts_checked": True,
            "existing_drafts_count": existing_drafts.count(),
            "outdated_drafts": outdated_drafts,
            "target_locale": target_locale,
            "document_id": document.id
        }

    def _generate_translation_urls(self, l10n_request: TranslationRequest) -> dict[str, str]:
        """Generate URLs for translation interfaces."""
        document = l10n_request.revision.document

        return {
            "select_locale_url": reverse("wiki.select_locale", args=[document.slug]),
            "translate_url": reverse("wiki.translate", args=[document.slug]),
            "show_translations_url": reverse("wiki.show_translations", args=[document.slug])
        }


class TranslationStrategyFactory:
    """Factory for creating and selecting translation strategies."""

    def __init__(self):
        self._strategies = {
            TranslationMethod.AI: AITranslationStrategy(),
            TranslationMethod.MANUAL: ManualTranslationStrategy(),
            TranslationMethod.HYBRID: HybridTranslationStrategy(),
        }

    def get_strategy(self, method: TranslationMethod) -> TranslationStrategy:
        """Get a specific strategy by method."""
        return self._strategies[method]

    def select_best_strategy(self, l10n_request: TranslationRequest) -> TranslationStrategy:
        """Select the best strategy based on business rules."""
        if l10n_request.target_locale in settings.AI_ENABLED_LOCALES:
            return self._strategies[TranslationMethod.AI]
        return self._strategies[TranslationMethod.MANUAL]

    def execute(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Execute translation workflow using appropriate strategy."""
        # TODO: Future enhancement - log all operations to database
        # This will track: revision_id, strategy_used, timestamps, outcomes

        strategy = self.select_best_strategy(l10n_request)
        result = strategy.translate(l10n_request)

        # TODO: Store result in database log
        # self._log_operation(l10n_request, result)

        return result
