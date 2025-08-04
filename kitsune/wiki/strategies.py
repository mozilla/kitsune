import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Now

from kitsune.users.models import Profile
from kitsune.wiki.config import REDIRECT_HTML, TYPO_SIGNIFICANCE
from kitsune.wiki.content_managers import (
    AIContentManager,
    HybridContentManager,
    ManualContentManager,
    NotificationType,
)
from kitsune.wiki.models import Document, Revision


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

    @abstractmethod
    def handle_due_tasks(self) -> None:
        """Handle any necessary tasks that accrue over time."""
        pass


class DueTaskCondition(models.IntegerChoices):
    """Available conditions for due tasks."""

    STALE = 0, "Stale machine translation"
    EXPIRED_REVIEW_GRACE_PERIOD = (
        1,
        "Machine translation whose review grace period has expired",
    )


@dataclass
class DueTaskResult:
    """Result of a due task."""

    revision: Revision
    condition: Any


class AbstractDueTasksHandler(ABC):
    """Handler of due tasks for a particular translation strategy."""

    @abstractmethod
    def run(self) -> None:
        pass


class DueTasksHandler(AbstractDueTasksHandler):
    """Handler of due tasks for a particular translation strategy."""

    def run(self) -> None:
        """Run all of the "handle_*" methods and record their results."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("handle_"):
                results = method()
                self.record(results)

    def record(self, results: list[DueTaskResult]) -> None:
        """Record a list of task results."""
        # TODO
        pass


class TranslationStrategy(AbstractTranslationStrategy):
    """Base class for translation strategies."""

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
        """Perform translation using this strategy."""
        return TranslationResult(success=True, method=TranslationMethod.MANUAL, metadata={})

    def handle_due_tasks(self) -> None:
        """Handle any necessary tasks that accrue over time."""
        pass


@dataclass
class AITranslationStrategy(TranslationStrategy):
    """AI-based translation strategy without human review."""

    content_manager: "AIContentManager" = field(init=False)

    def __post_init__(self):
        self.content_manager = AIContentManager()

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Perform AI translation."""
        # placeholder for AI translation logic

        return TranslationResult(
            success=True,
            method=TranslationMethod.AI,
            translated_content="",
            cost=0.0,
            quality_score=1.0,
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
            translated_content="",
            cost=0.0,
            quality_score=0.95,
            metadata={},
        )

    def handle_due_tasks(self) -> None:
        """
        Handle any machine translations that are stale, and that have
        expired review and post-review grace periods.
        """
        HybridDueTasksHandler().run()


@dataclass
class ManualTranslationStrategy(TranslationStrategy):
    """Manual translation workflow coordinator."""

    content_manager: "ManualContentManager" = field(init=False)

    def __post_init__(self):
        self.content_manager = ManualContentManager()

    def translate(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Execute manual translation strategy based on trigger."""
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
            success=False, method=TranslationMethod.MANUAL, error_message=message
        )

    def _handle_mark_ready_for_l10n(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Handle mark_ready_for_l10n trigger."""
        # Method will auto-detect that this is a standalone action and use current time
        self.content_manager.mark_ready_for_localization(
            l10n_request.revision, l10n_request.user, send_notifications=True
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
                l10n_request.revision, l10n_request.user, send_notifications=False
            )

        self.content_manager.fire_notifications(
            l10n_request.revision, [NotificationType.TRANSLATION_WORKFLOW], exclude_users
        )
        return TranslationResult(
            success=True,
            method=TranslationMethod.MANUAL,
            metadata={},
        )

    def create_revision(
        self,
        form_data,
        creator,
        document,
        based_on_id=None,
        base_rev=None,
        send_notifications=False,
    ):
        """Create a revision with optional notifications."""
        return self.content_manager.create_revision(
            form_data, creator, document, based_on_id, base_rev, send_notifications
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
        self._strategies_by_method = {
            TranslationMethod.AI: AITranslationStrategy(),
            TranslationMethod.MANUAL: ManualTranslationStrategy(),
            TranslationMethod.HYBRID: HybridTranslationStrategy(),
        }

    @property
    def strategies(self):
        return self._strategies_by_method.values()

    def get_strategy(self, method: TranslationMethod) -> TranslationStrategy:
        """Get a specific strategy by method."""
        return self._strategies_by_method[method]

    def select_best_strategy(self, l10n_request: TranslationRequest) -> TranslationStrategy:
        """Select the best strategy based on business rules."""
        if l10n_request.target_locale in settings.AI_ENABLED_LOCALES:
            return self._strategies_by_method[TranslationMethod.AI]
        return self._strategies_by_method[TranslationMethod.MANUAL]

    def execute(self, l10n_request: TranslationRequest) -> TranslationResult:
        """Execute translation workflow using appropriate strategy."""
        # TODO: Future enhancement - log all operations to database
        # This will track: revision_id, strategy_used, timestamps, outcomes

        strategy = self.select_best_strategy(l10n_request)
        result = strategy.translate(l10n_request)

        # TODO: Store result in database log
        # self._log_operation(l10n_request, result)

        return result


class HybridDueTasksHandler(DueTasksHandler):
    def __init__(self, doc: Document | None = None):
        self.sumo_bot = Profile.get_sumo_bot()
        self.review_grace_period = timedelta(days=settings.AI_REVIEW_GRACE_PERIOD)

        if doc:
            if doc.locale == settings.WIKI_DEFAULT_LANGUAGE:
                qs = Revision.objects.filter(document__parent=doc)
            else:
                qs = doc.revisions
        else:
            qs = Revision.objects.filter(
                document__parent__isnull=False,
                document__parent__is_localizable=True,
                document__parent__current_revision__isnull=False,
                document__parent__latest_localizable_revision__isnull=False,
            )

        # Limit to translations created by "sumo_bot" (machine translations) in enabled locales.
        unapproved_machine_translations = qs.filter(
            creator=self.sumo_bot,
            is_approved=False,
            document__locale__in=settings.AI_ENABLED_LOCALES,
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
        self.qs_stale = unapproved_machine_translations.filter(reviewed__isnull=True).filter(
            outdated | another_already_approved | translations_discontinued
        )

        fresh_machine_translations = unapproved_machine_translations.filter(
            based_on_id__gte=F("document__parent__latest_localizable_revision_id"),
        ).exclude(another_already_approved | translations_discontinued)

        if self.review_grace_period:
            self.qs_review_grace_period_expired = fresh_machine_translations.filter(
                reviewed__isnull=True,
                created__lt=Now() - self.review_grace_period,
            )
        else:
            self.qs_review_grace_period_expired = Revision.objects.none()

    def handle_stale_machine_translations(self) -> list[DueTaskResult]:
        """
        Reject stale machine translations.
        """
        results = []
        for rev in self.qs_stale:
            rev.is_approved = False
            rev.reviewer = self.sumo_bot
            rev.reviewed = datetime.now()
            rev.comment = "No longer relevant."
            rev.save()
            results.append(
                DueTaskResult(
                    revision=rev,
                    condition=DueTaskCondition.STALE,
                )
            )
        return results

    def handle_expired_review_grace_periods(self) -> list[DueTaskResult]:
        """
        Approve fresh, unreviewed machine translations whose grace period has expired.
        """
        results = []
        for rev in self.qs_review_grace_period_expired:
            rev.is_approved = True
            rev.reviewed = datetime.now()
            rev.reviewer = self.sumo_bot
            rev.comment = (
                "Automatically approved because it was not reviewed within"
                f" {settings.AI_REVIEW_GRACE_PERIOD} day(s)."
            )
            rev.save()
            results.append(
                DueTaskResult(
                    revision=rev,
                    condition=DueTaskCondition.EXPIRED_REVIEW_GRACE_PERIOD,
                )
            )
        return results
