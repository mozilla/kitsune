import json
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
from kitsune.wiki.tasks import translate as translate_task

SUPPORTED_TARGET_LOCALES = [
    locale for locale in settings.SUMO_LANGUAGES if locale not in ("xx", "en-US")
]


class TranslationMethod(models.TextChoices):
    """Available translation methods."""

    AI = "ai"
    MANUAL = "manual"
    HYBRID = "hybrid"
    VENDOR = "vendor"


@dataclass
class TranslationRequest:
    revision: Revision
    trigger: str
    user: User | None = None
    target_locale: str = ""
    method: Any = TranslationMethod.MANUAL
    priority: str = "normal"
    asynchronous: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_json(self):
        return json.dumps(
            {
                "revision_id": self.revision.id,
                "trigger": self.trigger,
                "user_id": self.user.id if self.user else None,
                "target_locale": self.target_locale,
                "method": self.method,
                "priority": self.priority,
                "asynchronous": self.asynchronous,
                "metadata": self.metadata,
            }
        )

    @classmethod
    def from_json(cls, data_as_json):
        data = json.loads(data_as_json)
        if user_id := data.pop("user_id", None):
            data["user"] = User.objects.get(id=user_id)
        data["revision"] = Revision.objects.select_related("document").get(
            id=data.pop("revision_id")
        )
        return cls(**data)


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

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Execute manual translation strategy based on trigger."""
        return TranslationResult(success=True)

    def _log_operation(
        self, l10n_request: TranslationRequest, translation_result: TranslationResult
    ) -> None:
        # TODO: Future enhancement - log all operations to database
        # This will track: revision_id, strategy_used, timestamps, outcomes
        # self._log_operation(l10n_request, result)
        pass


@dataclass
class ManualTranslationStrategy(TranslationStrategy):
    """Manual translation workflow coordinator."""

    content_manager: "ManualContentManager" = field(init=False)

    def __post_init__(self):
        self.content_manager = ManualContentManager()

    def _handle_mark_ready_for_l10n(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Handle mark_ready_for_l10n trigger."""
        # Method will auto-detect that this is a standalone action and use current time
        self.content_manager.mark_ready_for_localization(
            l10n_request.revision,
            l10n_request.user,
            send_notifications=True,
        )

        result = TranslationResult(
            success=True,
            method=TranslationMethod.MANUAL,
            revision=l10n_request.revision,
            metadata={},
        )
        self._log_operation(l10n_request, result)
        return result

    def _handle_review_revision(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Handle review_revision trigger - sends approval notifications and conditionally handles localization."""
        # Mark as ready for localization - method will auto-detect if this is part of review workflow
        self.content_manager.mark_ready_for_localization(
            l10n_request.revision,
            l10n_request.user,
            send_notifications=False,
        )

        exclude_users = []
        if l10n_request.revision.creator:
            exclude_users.append(l10n_request.revision.creator)
        if l10n_request.user:
            exclude_users.append(l10n_request.user)

        self.content_manager.fire_notifications(
            l10n_request.revision, [NotificationType.TRANSLATION_WORKFLOW], exclude_users
        )
        result = TranslationResult(
            success=True,
            method=TranslationMethod.MANUAL,
            revision=l10n_request.revision,
            metadata={},
        )
        self._log_operation(l10n_request, result)
        return result

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform translation using this strategy."""
        revision = l10n_request.revision

        if not self.can_handle(l10n_request):
            result = TranslationResult(
                success=False,
                method=TranslationMethod.MANUAL,
                revision=revision,
                error_message="Revision cannot be marked as ready for localization",
            )
            self._log_operation(l10n_request, result)
            return result

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

        result = TranslationResult(
            success=False,
            method=TranslationMethod.MANUAL,
            revision=revision,
            error_message=message,
            metadata={},
        )
        self._log_operation(l10n_request, result)
        return result


@dataclass
class AITranslationStrategy(TranslationStrategy):
    """AI-based translation strategy without human review."""

    content_manager: "AIContentManager" = field(init=False)

    def __post_init__(self):
        self.content_manager = AIContentManager()

    def translate(
        self, l10n_request: TranslationRequest, publish: bool = True
    ) -> TranslationResult:
        """Perform AI translation."""
        doc = l10n_request.revision.document

        translated_content = llm_translate(doc=doc, target_locale=l10n_request.target_locale)

        data = {
            "content": translated_content["content"]["translation"],
            "summary": translated_content["summary"]["translation"],
            "keywords": translated_content["keywords"]["translation"],
            "target_locale": l10n_request.target_locale,
            "translated_content": translated_content,
        }

        rev = self.content_manager.create_revision(data, doc, send_notifications=True)
        if publish:
            rev = self.content_manager.publish_revision(rev)

        result = TranslationResult(
            success=True,
            method=l10n_request.method,
            revision=rev,
            metadata={
                "explanation": {
                    "content": translated_content["content"]["explanation"],
                    "summary": translated_content["summary"]["explanation"],
                    "keywords": translated_content["keywords"]["explanation"],
                    "title": translated_content.get("title", {}).get("explanation"),
                }
            },
        )
        self._log_operation(l10n_request, result)
        return result


@dataclass
class HybridTranslationStrategy(TranslationStrategy):
    """Hybrid translation strategy (AI + Human review)."""

    content_manager: "HybridContentManager" = field(init=False)

    def __post_init__(self):
        self.content_manager = HybridContentManager()

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform hybrid translation."""
        result = AITranslationStrategy().translate(l10n_request, publish=False)
        result.method = TranslationMethod.HYBRID
        return result


class TranslationStrategyFactory:
    """Factory for creating and selecting translation strategies."""

    def __init__(self):
        self._strategies = {
            TranslationMethod.AI: AITranslationStrategy(),
            TranslationMethod.MANUAL: ManualTranslationStrategy(),
            TranslationMethod.HYBRID: HybridTranslationStrategy(),
        }

    def get_strategy(self, method: TranslationMethod | str) -> TranslationStrategy:
        """Get a specific strategy by method."""
        if isinstance(method, str):
            method = TranslationMethod(method)
        return self._strategies[method]

    def select_best_strategy(self, l10n_request: TranslationRequest) -> TranslationStrategy:
        """Select the best strategy based on business rules."""
        if l10n_request.target_locale in settings.AI_ENABLED_LOCALES:
            return self.get_strategy(TranslationMethod.AI)
        elif l10n_request.target_locale in settings.HYBRID_ENABLED_LOCALES:
            return self.get_strategy(TranslationMethod.HYBRID)
        return self.get_strategy(TranslationMethod.MANUAL)

    def execute(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Execute translation workflow using appropriate strategy."""
        strategy = self.select_best_strategy(l10n_request)

        if l10n_request.asynchronous and (l10n_request.method != TranslationMethod.MANUAL):
            translate_task.delay(l10n_request.as_json())

            return TranslationResult(
                success=True,
                method=l10n_request.method,
                revision=l10n_request.revision,
                metadata={"status": "queued_for_processing"},
            )
        else:
            return strategy.translate(l10n_request)
