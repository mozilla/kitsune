from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from kitsune.llm.l10n.translator import translate as llm_translate
from kitsune.wiki.config import TYPO_SIGNIFICANCE
from kitsune.wiki.content_managers import (
    AIContentManager,
    HybridContentManager,
    ManualContentManager,
    NotificationType,
    WikiContentManager,
)
from kitsune.wiki.models import Revision


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
    target_locale: str = ""
    method: Any = TranslationMethod.MANUAL
    priority: str = "normal"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationResult:
    """Result of translation operation."""

    success: bool
    method: Any = None
    revision: Revision | None = None
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


@dataclass
class TranslationStrategy(AbstractTranslationStrategy):
    """Base class for translation strategies."""

    content_manager: "WikiContentManager" = field(init=False)

    def __post_init__(self):
        self.content_manager = WikiContentManager()


    def _is_localizable_document(self, revision: Revision) -> bool:
        """Check if a document is localizable."""
        try:
            document = revision.document
        except revision.__class__.document.RelatedObjectDoesNotExist:
            return False

        return all(
            [
                document.is_localizable,
                document.locale == settings.WIKI_DEFAULT_LANGUAGE,
                revision.is_approved,
                not revision.significance or revision.significance > TYPO_SIGNIFICANCE,
            ]
        )

    def can_handle(self, l10n_request: TranslationRequest) -> bool:
        """Check if this strategy can handle the request (basic validation)."""
        revision = l10n_request.revision
        return self._is_localizable_document(revision)

    @classmethod
    def can_handle_revision(cls, revision: Revision) -> bool:
        """Check if a revision meets basic criteria for l10n."""
        return cls()._is_localizable_document(revision)

    def _handle_mark_ready_for_l10n(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Handle mark_ready_for_l10n trigger."""
        # Method will auto-detect that this is a standalone action and use current time
        self.content_manager.mark_ready_for_localization(
            l10n_request.revision,
            l10n_request.user,
            send_notifications=True,
        )

        return TranslationResult(
            success=True,
            method=TranslationMethod.MANUAL,
            metadata={},
        )

    def _handle_review_revision(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Handle review_revision trigger - sends approval notifications and conditionally handles localization."""
        exclude_users = []
        if l10n_request.revision.creator:
            exclude_users.append(l10n_request.revision.creator)
        if l10n_request.user:
            exclude_users.append(l10n_request.user)

        if self.can_handle(l10n_request):
            # Mark as ready for localization - method will auto-detect if this is part of review workflow
            self.content_manager.mark_ready_for_localization(
                l10n_request.revision,
                l10n_request.user,
                send_notifications=False,
            )

        self.content_manager.fire_notifications(
            l10n_request.revision, [NotificationType.TRANSLATION_WORKFLOW], exclude_users
        )
        return TranslationResult(
            success=True,
            method=TranslationMethod.MANUAL,
            metadata={},
        )

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform translation using this strategy."""

        if not self.can_handle(l10n_request):
            return TranslationResult(
                success=False,
                method=TranslationMethod.MANUAL,
                error_message="Revision cannot be marked as ready for localization",
            )

        revision = l10n_request.revision
        message = None

        match l10n_request.trigger:
            case "mark_ready_for_l10n":
                if not revision.is_ready_for_localization:
                    return self._handle_mark_ready_for_l10n(l10n_request)
                message = "Revision is already ready for localization"
            case "review_revision":
                return self._handle_review_revision(l10n_request)
            case _:
                message = f"Unknown trigger: {l10n_request.trigger}"

        return TranslationResult(
            success=False, method=TranslationMethod.MANUAL, revision=revision, error_message=message, metadata={}
        )



@dataclass
class AITranslationStrategy(TranslationStrategy):
    """AI-based translation strategy without human review."""

    content_manager: "AIContentManager" = field(init=False)

    def __post_init__(self):
        self.content_manager = AIContentManager()



    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform AI translation."""
        # Base class handles the revision marking and notifications.
        result = super().translate(l10n_request)

        if not result.success:
            return result

        doc = l10n_request.revision.document

        # TODO: This should be done asynchronously.
        translated_content = llm_translate(doc=doc, target_locale=l10n_request.target_locale)

        data = {
            "content": translated_content["content"]["translation"],
            "summary": translated_content["summary"]["translation"],
            "keywords": translated_content["keywords"]["translation"],
            "target_locale": l10n_request.target_locale,
            "translated_content": translated_content,
        }

        rev = self.content_manager.publish_revision(
            self.content_manager.create_revision(data, doc, send_notifications=True),
        )

        return TranslationResult(
            success=True,
            method=TranslationMethod.AI,
            revision=rev,
            metadata={},
        )


@dataclass
class HybridTranslationStrategy(TranslationStrategy):
    """Hybrid translation strategy (AI + Human review)."""

    content_manager: "HybridContentManager" = field(init=False)

    def __post_init__(self):
        self.content_manager = HybridContentManager()

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform hybrid translation."""

        # placeholder for hybrid translation logic
        return TranslationResult(
            success=True,
            method=TranslationMethod.HYBRID,
            revision=l10n_request.revision,
            cost=0.0,
            quality_score=0.95,
            metadata={},
        )


@dataclass
class ManualTranslationStrategy(TranslationStrategy):
    """Manual translation workflow coordinator."""

    content_manager: "ManualContentManager" = field(init=False)

    def __post_init__(self):
        self.content_manager = ManualContentManager()

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Execute manual translation strategy based on trigger."""
        return super().translate(l10n_request)

    def create_revision(
        self,
        data,
        document,
        creator,
        based_on_id=None,
        base_rev=None,
        send_notifications=False,
    ):
        """Create a revision with optional notifications."""
        return self.content_manager.create_revision(
            data, document, creator, based_on_id, base_rev, send_notifications
        )

    def save_draft(self, user, parent_doc, target_locale, draft_data):
        """Convenience method - delegates to content_manager."""
        return self.content_manager.save_draft(user, parent_doc, target_locale, draft_data)

    def get_draft(self, user, parent_doc, target_locale):
        """Convenience method - delegates to content_manager."""
        return self.content_manager.get_draft(user, parent_doc, target_locale)

    def restore_draft(self, draft_id, user):
        """Convenience method - delegates to content_manager."""
        return self.content_manager.restore_draft(draft_id, user)

    def discard_draft(self, draft_id, user):
        """Convenience method - delegates to content_manager."""
        return self.content_manager.discard_draft(draft_id, user)


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
