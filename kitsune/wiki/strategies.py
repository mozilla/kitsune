import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta
from functools import cached_property
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Now

from kitsune.llm.l10n.translator import translate as llm_translate
from kitsune.users.models import Profile
from kitsune.wiki.config import REDIRECT_HTML, TYPO_SIGNIFICANCE
from kitsune.wiki.content_managers import (
    AIContentManager,
    HybridContentManager,
    ManualContentManager,
    WikiContentManager,
)
from kitsune.wiki.models import Document, Revision
from kitsune.wiki.tasks import translate as translate_task


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
        """Check if this strategy can handle the request."""
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
        self.content_manager.mark_ready_for_localization(l10n_request.revision, l10n_request.user)

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
            l10n_request.revision, l10n_request.user, is_review_workflow=True
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
            created__lt=Now() - timedelta(days=settings.HYBRID_REVIEW_GRACE_PERIOD),
        ).exclude(another_already_approved | translations_discontinued)

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform hybrid translation."""
        result = AITranslationStrategy().translate(l10n_request, publish=False)
        result.method = TranslationMethod.HYBRID
        return result

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

        grace_period = f"{settings.HYBRID_REVIEW_GRACE_PERIOD} day(s)"

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


class TranslationStrategyFactory:
    """Factory for creating and selecting translation strategies."""

    @cached_property
    def _strategies(self):
        return {
            TranslationMethod.AI: AITranslationStrategy(),
            TranslationMethod.MANUAL: ManualTranslationStrategy(),
            TranslationMethod.HYBRID: HybridTranslationStrategy(),
        }

    def get_strategy(self, method: TranslationMethod | str) -> TranslationStrategy:
        """Get a specific strategy by method."""
        if isinstance(method, str):
            method = TranslationMethod(method)
        return self._strategies[method]

    def get_method_for_locale(self, locale: str) -> TranslationMethod:
        """Determine the appropriate translation method for a given locale."""
        if locale in settings.AI_ENABLED_LOCALES:
            return TranslationMethod(TranslationMethod.AI)
        elif locale in settings.HYBRID_ENABLED_LOCALES:
            return TranslationMethod(TranslationMethod.HYBRID)
        return TranslationMethod(TranslationMethod.MANUAL)

    def select_best_strategy(self, l10n_request: TranslationRequest) -> TranslationStrategy:
        """Select the best strategy based on business rules."""
        method = self.get_method_for_locale(l10n_request.target_locale)
        return self.get_strategy(method)

    def execute(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Execute translation workflow using appropriate strategy."""
        if l10n_request.method == TranslationMethod.MANUAL:
            manual_result = self.get_strategy(TranslationMethod.MANUAL).translate(l10n_request)
            if manual_result.success:
                for locales, method in [
                    (settings.AI_ENABLED_LOCALES, TranslationMethod.AI),
                    (settings.HYBRID_ENABLED_LOCALES, TranslationMethod.HYBRID),
                ]:
                    for locale in locales:
                        self.execute(
                            TranslationRequest(
                                revision=l10n_request.revision,
                                trigger="translate",
                                target_locale=locale,
                                method=method,
                                user=l10n_request.user,
                                asynchronous=True,
                            )
                        )
            return manual_result
        # For explicit AI/Hybrid requests, use existing single-strategy logic
        strategy = self.select_best_strategy(l10n_request)
        if l10n_request.asynchronous and (l10n_request.method != TranslationMethod.MANUAL):
            from kitsune.wiki.tasks import translate as translate_task

            translate_task.delay(l10n_request.as_json())
            return TranslationResult(
                success=True,
                method=l10n_request.method,
                revision=l10n_request.revision,
                metadata={"status": "queued_for_processing"},
            )
        else:
            return strategy.translate(l10n_request)
