from typing import Any

from kitsune.llm.l10n.strategies import (
    TranslationMethod,
    TranslationRequest,
    TranslationStrategyFactory,
)
from kitsune.wiki.models import Revision


class TranslationService:
    """Service for orchestrating translation operations."""

    def __init__(self):
        self.factory = TranslationStrategyFactory()

    def translate_document(self, revision: Revision, target_locales: list[str],
                          method: TranslationMethod | None = None) -> dict[str, Any]:
        """
        Translate a document to multiple target locales.
        Args:
            revision: The revision to translate
            target_locales: List of target locales
            method: Optional specific method, otherwise auto-selects best method
        Returns:
            Dictionary with translation results for each locale
        """
        results = {}

        for locale in target_locales:
            # Create translation request
            request = TranslationRequest(
                revision=revision,
                target_locale=locale,
                method=method or TranslationMethod.AI,
                priority="normal",
                metadata={"source_locale": revision.document.locale}
            )

            # Select strategy (either specified or auto-selected)
            if method:
                strategy = self.factory.get_strategy(method)
            else:
                strategy = self.factory.select_best_strategy(request)

            # Perform translation
            result = strategy.translate(request)
            results[locale] = {
                "success": result.success,
                "method": result.method.value if result.method else None,
                "method_display": result.method.label if result.method else None,
                "cost": result.cost,
                "quality_score": result.quality_score,
                "error": result.error_message,
                "metadata": result.metadata
            }
        return results

    def get_translation_estimate(self, revision: Revision, target_locales: list[str]) -> dict[str, Any]:
        """
        Get cost and method estimates for translation.
        Args:
            revision: The revision to translate
            target_locales: List of target locales
        Returns:
            Dictionary with estimates for each locale
        """
        estimates = {}

        for locale in target_locales:
            # Simple placeholder implementation
            estimates[locale] = {
                "recommended_method": "AI Translation",
                "cost_estimate": 0.0,
                "can_handle": True,
                "estimated_time": "5-10 minutes"
            }

        return estimates
