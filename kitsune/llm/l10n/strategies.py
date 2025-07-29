from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings
from django.db import models

from kitsune.wiki.models import Revision


class TranslationMethod(models.TextChoices):
    """Available translation methods."""
    AI = "ai", "AI Translation"
    VENDOR = "vendor", "Vendor Translation"
    HYBRID = "hybrid", "AI + Human Review"
    MANUAL = "manual", "Manual Translation"


@dataclass
class TranslationRequest:
    """Request object for translation operations."""
    revision: Revision
    target_locale: str
    method: Any
    priority: str = "normal"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationResult:
    """Result object for translation operations."""
    success: bool
    translated_content: str | None = None
    method: Any = None
    cost: float = 0.0
    quality_score: float = 0.0
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TranslationStrategy(ABC):
    """Abstract base class for translation strategies."""

    @abstractmethod
    def translate(self, request: TranslationRequest) -> TranslationResult:
        """Translate content using this strategy."""
        pass

    @abstractmethod
    def can_handle(self, request: TranslationRequest) -> bool:
        """Check if this strategy can handle the request."""
        pass

    @abstractmethod
    def get_cost_estimate(self, request: TranslationRequest) -> float:
        """Get estimated cost for this translation."""
        pass


class AITranslationStrategy(TranslationStrategy):
    """AI/LLM-based translation strategy."""

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """Translate using AI/LLM."""
        try:
            from kitsune.llm.l10n.translator import translate
            result = translate(request.revision.document, request.target_locale)

            # Ensure translated_content is a string
            translated_content = result.get("content", "")
            if not isinstance(translated_content, str):
                translated_content = str(translated_content)

            return TranslationResult(
                success=True,
                translated_content=translated_content,
                method=TranslationMethod.AI,
                cost=0.0,
                quality_score=0.85,
                metadata={"ai_model": "gpt-4", "result": result}
            )
        except Exception as e:
            return TranslationResult(
                success=False,
                method=TranslationMethod.AI,
                error_message=str(e)
            )

    def can_handle(self, request: TranslationRequest) -> bool:
        """AI can handle most content types."""
        return True

    def get_cost_estimate(self, request: TranslationRequest) -> float:
        """AI translation is typically free."""
        return 0.0

    def _create_translated_revision(self, request: TranslationRequest, result: TranslationResult) -> Revision:
        """Create a translated revision."""
        # TODO: Implement revision creation
        # Should create the revision object
        return Revision.objects.first()


class HybridTranslationStrategy(TranslationStrategy):
    """AI + Human review translation strategy."""

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """Translate using AI + human review workflow."""
        try:
            # Step 1: AI translation
            ai_strategy = AITranslationStrategy()
            ai_result = ai_strategy.translate(request)

            if not ai_result.success:
                return ai_result

            review_task = self._create_review_task(request, ai_result)

            return TranslationResult(
                success=True,
                translated_content=ai_result.translated_content,
                method=TranslationMethod.HYBRID,
                cost=10.0,
                quality_score=0.95,
                metadata={
                    "ai_result": ai_result.metadata,
                    "review_task_id": review_task.get("id"),
                    "status": "pending_review"
                }
            )
        except Exception as e:
            return TranslationResult(
                success=False,
                method=TranslationMethod.HYBRID,
                error_message=str(e)
            )

    def can_handle(self, request: TranslationRequest) -> bool:
        """Hybrid is the default strategy for all AI enabled locales."""
        return True

    def get_cost_estimate(self, request: TranslationRequest) -> float:
        """Estimate cost for hybrid approach."""
        # TODO: Implement cost estimation for hybrid approach
        return 0.0

    def _create_review_task(self, request: TranslationRequest, ai_result: TranslationResult) -> dict[str, Any]:
        """Create a review task for human translator."""
        # Placeholder for task creation
        # notify and create the revision?
        return {}


class ManualTranslationStrategy(TranslationStrategy):
    """Manual human translation strategy."""

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """Create manual translation task."""
        try:
            manual_task = self._create_manual_task(request)

            return TranslationResult(
                success=True,
                translated_content="",
                method=TranslationMethod.MANUAL,
                cost=50.0,
                quality_score=0.98,
                metadata={
                    "task_id": manual_task.get("id"),
                    "status": "assigned_to_translator",
                    "estimated_completion": manual_task.get("estimated_completion")
                }
            )
        except Exception as e:
            return TranslationResult(
                success=False,
                method=TranslationMethod.MANUAL,
                error_message=str(e)
            )

    def can_handle(self, request: TranslationRequest) -> bool:
        """Manual translation can handle any content."""
        return True

    def get_cost_estimate(self, request: TranslationRequest) -> float:
        """Estimate cost for manual translation."""
        return 0.0

    def _create_manual_task(self, request: TranslationRequest) -> dict[str, Any]:
        """Create a manual translation task."""
        # Placeholder for task creation
        return {}


class TranslationStrategyFactory:
    """Factory for creating translation strategies."""

    def __init__(self):
        self._strategies = {
            TranslationMethod.AI: AITranslationStrategy(),
            TranslationMethod.HYBRID: HybridTranslationStrategy(),
            TranslationMethod.MANUAL: ManualTranslationStrategy(),
        }

    def get_strategy(self, method: TranslationMethod) -> TranslationStrategy:
        """Get strategy for the specified method."""
        if method not in self._strategies:
            raise ValueError(f"Unknown translation method: {method}")
        return self._strategies[method]

    def select_best_strategy(self, request: TranslationRequest) -> TranslationStrategy:
        """Select the best strategy based on business rules."""
        if request.target_locale in settings.AI_ENABLED_LOCALES:
            return self._strategies[TranslationMethod.AI]
        return self._strategies[TranslationMethod.MANUAL]
