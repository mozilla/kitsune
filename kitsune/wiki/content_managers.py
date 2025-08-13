from collections.abc import Iterable
from datetime import datetime
from typing import Any

from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Q, QuerySet

from kitsune.users.models import Profile
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.wiki.events import (
    ApprovedOrReadyUnion,
    EditDocumentEvent,
    ReadyRevisionEvent,
    ReviewableRevisionInLocaleEvent,
)
from kitsune.wiki.models import Document, DraftRevision, Revision
from kitsune.wiki.tasks import (
    render_document_cascade,
    send_contributor_notification,
    send_reviewed_notification,
)


class NotificationType(models.TextChoices):
    """Types of notifications that can be fired by content managers."""

    CONTENT_CREATION = "content_creation", "Content Creation"
    TRANSLATION_WORKFLOW = "translation_workflow", "Translation Workflow"
    READY_FOR_L10N = "ready_for_l10n", "Ready for Localization"
    REVIEW_WORKFLOW = "review_workflow", "Review Workflow"


class WikiContentManager:
    """Manages both draft revisions and published revisions for wiki content."""

    def save_draft(
        self, user, parent_doc, target_locale: str, draft_data: dict[str, Any]
    ) -> DraftRevision:
        """Save or update a draft revision for the given user, document, and locale.

        Args:
            user: The user creating the draft
            parent_doc: The parent document being translated
            target_locale: The target locale for translation
            draft_data: Dictionary containing draft content (title, slug, content, summary, keywords, based_on)
        Returns:
            DraftRevision: The created or updated draft revision
        """
        draft, created = DraftRevision.objects.update_or_create(
            creator=user, document=parent_doc, locale=target_locale, defaults=draft_data
        )
        return draft

    def get_draft(self, user, parent_doc, target_locale: str) -> DraftRevision | None:
        """Get existing draft for user, document, and locale.

        Args:
            user: The user
            parent_doc: The parent document
            target_locale: The target local
        Returns:
            DraftRevision or None: The existing draft if found
        """
        return DraftRevision.objects.filter(
            creator=user, document=parent_doc, locale=target_locale
        ).first()

    def restore_draft(self, draft_id: int, user) -> dict[str, Any]:
        """Restore draft content for form initialization.

        Args:
            draft_id: ID of the draft to restore
            user: The user requesting restoration
        Returns:
            dict: Draft data for initializing forms
        """
        try:
            draft = DraftRevision.objects.get(id=draft_id, creator=user)
        except DraftRevision.DoesNotExist:
            raise ValueError(f"Draft {draft_id} not found for user {user.username}")

        return {
            "title": draft.title,
            "slug": draft.slug,
            "content": draft.content,
            "summary": draft.summary,
            "keywords": draft.keywords,
            "based_on": draft.based_on.id if draft.based_on else None,
        }

    def discard_draft(self, draft_id: int, user) -> bool:
        """Delete a draft revision.

        Args:
            draft_id: ID of the draft to delete
            user: The user requesting deletion
        Returns:
            bool: True if draft was successfully deleted
        """
        try:
            DraftRevision.objects.get(id=draft_id, creator=user).delete()
        except DraftRevision.DoesNotExist:
            return False
        else:
            return True

    def publish_draft(
        self, draft_id: int, user, data: dict[str, Any], based_on_id=None, base_rev=None
    ) -> Revision:
        """Convert a draft to a published revision and delete the draft.

        Args:
            draft_id: ID of the draft to publish
            user: The user publishing the draft
            data: Data for revision creation
            based_on_id: Optional ID of the revision this is based on
            base_rev: Optional base revision object
        Returns:
            Revision: The created revision
        """
        try:
            draft = DraftRevision.objects.select_related("document").get(id=draft_id, creator=user)
        except DraftRevision.DoesNotExist:
            raise ValueError(f"Draft {draft_id} not found for user {user.username}")

        revision = self.create_revision(data, user, draft.document, based_on_id, base_rev)
        draft.delete()
        return revision

    def create_revision(
        self,
        data: dict[str, Any],
        document,
        creator,
        based_on_id=None,
        base_rev=None,
        send_notifications=False,
    ) -> Revision:
        """Create a new revision from data with validation and permissions.

        Args:
            data: Dictionary containing revision data (content, summary, keywords, etc.)
            creator: The user creating the revision
            document: The document this revision belongs to
            based_on_id: Optional ID of the revision this is based on
            base_rev: Optional base revision object for keyword permission checking
            send_notifications: Whether to send content creation notifications
        Returns:
            Revision: The created revision
        """
        revision = Revision(**data)
        revision.document = document
        revision.creator = creator
        revision.created = datetime.now()

        if based_on_id:
            revision.based_on_id = based_on_id

        # Handle keyword permissions - if user can't edit keywords, preserve old value
        if base_rev and not document.allows(creator, "edit_keywords"):
            revision.keywords = base_rev.keywords

        revision.save()
        if send_notifications:
            self.fire_notifications(revision, [NotificationType.CONTENT_CREATION])
        return revision

    def publish_revision(
        self, revision: Revision, user, comment=None, send_notifications=True
    ) -> Revision:
        """Publish (approve) a revision."""
        return self.review_revision(revision, user, True, comment, send_notifications)

    def reject_revision(self, revision: Revision, user, comment=None) -> Revision:
        """Reject (disapprove) a revision."""
        return self.review_revision(revision, user, False, comment, send_notifications=False)

    def review_revision(
        self,
        revision: Revision,
        reviewer: User,
        approve: bool,
        comment: str | None = None,
        send_notifications=True,
    ) -> Revision:
        """Review (approve or reject) a revision.

        Args:
            revision: The revision to publish
            reviewer: The user reviewing the revision
            approve: Whether the revision is approved or not
            comment: An optional comment to assign to the revision
            send_notifications: Whether to send content creation notifications
        """
        revision.is_approved = approve
        revision.reviewed = datetime.now()
        revision.reviewer = reviewer
        if comment:
            revision.comment = comment
        revision.save()

        if approve and send_notifications:
            exclude_users = [reviewer] if reviewer else []
            self.fire_notifications(
                revision, [NotificationType.TRANSLATION_WORKFLOW], exclude_users
            )
        return revision

    def fire_notifications(
        self, revision: Revision, notification_types, exclude_users=None, comment=None
    ):
        """Unified notification dispatcher - figures out what notifications to fire."""
        exclude_users = exclude_users or [revision.creator]

        for notif_type in notification_types:
            match notif_type:
                case NotificationType.CONTENT_CREATION:
                    ReviewableRevisionInLocaleEvent(revision).fire(exclude=exclude_users)
                    EditDocumentEvent(revision).fire(exclude=exclude_users)
                case NotificationType.TRANSLATION_WORKFLOW:
                    ApprovedOrReadyUnion(revision).fire(exclude=exclude_users)
                case NotificationType.READY_FOR_L10N:
                    ReadyRevisionEvent(revision).fire(exclude=exclude_users)
                case NotificationType.REVIEW_WORKFLOW:
                    send_reviewed_notification.delay(revision.id, comment)
                    send_contributor_notification.delay(revision.id, comment)

    def mark_ready_for_localization(
        self, revision: Revision, user=None, send_notifications=True
    ) -> None:
        """Mark a revision as ready for localization and optionally send notifications."""
        revision.is_ready_for_localization = True
        revision.readied_for_localization = (
            datetime.now() if send_notifications else revision.reviewed
        )
        if user:
            revision.readied_for_localization_by = user
        revision.save()

        if send_notifications:
            exclude_users = [user] if user else []
            self.fire_notifications(revision, [NotificationType.READY_FOR_L10N], exclude_users)


class ManualContentManager(WikiContentManager):
    """Content manager for manual translation workflow."""

    pass


class AIContentManager(WikiContentManager):
    """Content manager for AI translation workflow."""

    def create_revision(
        self,
        data: dict[str, Any],
        document,
        creator=None,
        based_on_id=None,
        base_rev=None,
        send_notifications=False,
    ) -> Revision:
        """Create a revision with AI-specific handling for document creation.

        This method handles both document creation and revision creation for AI translations.
        """
        target_locale = data.pop("target_locale", None)
        translated_content = data.pop("translated_content", None)

        if target_locale and translated_content:
            title = (
                document.title
                if document.is_template
                else translated_content.get("title", {}).get("translation")
            )

            target_doc, _ = Document.objects.get_or_create(
                parent=document,
                locale=target_locale,
                defaults={
                    "title": title,
                    "slug": document.slug,
                    "is_localizable": False,
                    "category": document.category,
                    "is_template": document.is_template,
                    "allow_discussion": document.allow_discussion,
                },
            )

            document = target_doc

            if not based_on_id:
                based_on_id = document.parent.latest_localizable_revision_id

            data["created"] = datetime.now()

        return super().create_revision(
            data, document, Profile.get_sumo_bot(), based_on_id, base_rev, send_notifications
        )

    def publish_revision(
        self, revision: Revision, user=None, comment=None, send_notifications=True
    ) -> Revision:
        """Publish (approve) a revision using the sumo bot."""
        user = user or Profile.get_sumo_bot()
        rev = super().publish_revision(revision, user, comment, send_notifications)
        self.fire_notifications(rev, [NotificationType.REVIEW_WORKFLOW])
        render_document_cascade.delay(rev.document.id)
        return rev


class HybridContentManager(AIContentManager):
    """Content manager for hybrid translation workflow."""

    def __init__(self):
        unreviewed_translations = Revision.objects.filter(
            is_approved=False,
            reviewed__isnull=True,
            document__parent__isnull=False,
            document__parent__is_localizable=True,
            document__parent__current_revision__isnull=False,
            document__parent__latest_localizable_revision__isnull=False,
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

        # Unreviewed translations that are no longer useful.
        self._qs_stale_translations = unreviewed_translations.filter(
            outdated | another_already_approved | translations_discontinued
        )

        # Unreviewed translations that are still fresh and useful.
        self._qs_fresh_translations = unreviewed_translations.filter(
            based_on_id__gte=F("document__parent__latest_localizable_revision_id")
        ).exclude(another_already_approved | translations_discontinued)

    def get_stale_translations(
        self,
        creator: User | None = None,
        locales: Iterable[str] | None = None,
        **extra_filters: dict[str, Any],
    ) -> QuerySet[Revision]:
        """Unreviewed translations that are no longer useful."""
        filters: dict[str, Any] = {"creator": creator or Profile.get_sumo_bot()}
        if locales:
            filters.update(document__locale__in=locales)
        return self._qs_stale_translations.filter(**filters, **extra_filters)

    def get_fresh_translations(
        self,
        creator: User | None = None,
        locales: Iterable[str] | None = None,
        **extra_filters: dict[str, Any],
    ) -> QuerySet[Revision]:
        """Unreviewed translations that are still fresh and useful."""
        filters: dict[str, Any] = {"creator": creator or Profile.get_sumo_bot()}
        if locales:
            filters.update(document__locale__in=locales)
        return self._qs_fresh_translations.filter(**filters, **extra_filters)

    def reject_revision(self, revision: Revision, user=None, comment=None) -> Revision:
        """Reject (disapprove) a revision using the sumo bot."""
        user = user or Profile.get_sumo_bot()
        rev = super().reject_revision(revision, user, comment)
        self.fire_notifications(rev, [NotificationType.REVIEW_WORKFLOW])
        return rev
