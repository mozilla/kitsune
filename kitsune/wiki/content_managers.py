from typing import Any

from django.db import models

from kitsune.wiki.events import (
    ApprovedOrReadyUnion,
    EditDocumentEvent,
    ReadyRevisionEvent,
    ReviewableRevisionInLocaleEvent,
)
from kitsune.wiki.models import DraftRevision, Revision


class NotificationType(models.TextChoices):
    """Types of notifications that can be fired by content managers."""
    CONTENT_CREATION = "content_creation", "Content Creation"
    TRANSLATION_WORKFLOW = "translation_workflow", "Translation Workflow"
    READY_FOR_L10N = "ready_for_l10n", "Ready for Localization"


class WikiContentManager:
    """Manages both draft revisions and published revisions for wiki content."""

    def save_draft(self, user, parent_doc, target_locale: str, draft_data: dict[str, Any]) -> DraftRevision:
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

    def create_revision(self, form_data: dict[str, Any], creator, document, based_on_id=None, base_rev=None, send_notifications=False) -> Revision:
        """Create a new revision from form data with validation and permissions.

        Args:
            form_data: Dictionary containing revision data (content, summary, keywords, etc.)
            creator: The user creating the revision
            document: The document this revision belongs to
            based_on_id: Optional ID of the revision this is based on
            base_rev: Optional base revision object for keyword permission checking
            send_notifications: Whether to send content creation notifications
        Returns:
            Revision: The created revision
        """
        revision = Revision(**form_data)
        revision.document = document
        revision.creator = creator

        if based_on_id:
            revision.based_on_id = based_on_id

        # Handle keyword permissions - if user can't edit keywords, preserve old value
        if base_rev and not document.allows(creator, "edit_keywords"):
            revision.keywords = base_rev.keywords

        revision.save()
        if send_notifications:
            self.fire_notifications(revision, [NotificationType.CONTENT_CREATION])
        return revision

    def publish_draft(self, draft_id: int, user, form_data: dict[str, Any], based_on_id=None, base_rev=None) -> Revision:
        """Convert a draft to a published revision and delete the draft.

        Args:
            draft_id: ID of the draft to publish
            user: The user publishing the draft
            form_data: Form data for revision creation
            based_on_id: Optional ID of the revision this is based on
            base_rev: Optional base revision object
        Returns:
            Revision: The created revision
        """
        try:
            draft = DraftRevision.objects.select_related("document").get(id=draft_id, creator=user)
        except DraftRevision.DoesNotExist:
            raise ValueError(f"Draft {draft_id} not found for user {user.username}")

        revision = self.create_revision(form_data, user, draft.document, based_on_id, base_rev)
        draft.delete()
        return revision

    def fire_notifications(self, revision: Revision, notification_types, exclude_users=None):
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

    def mark_ready_for_localization(self, revision: Revision, user=None, send_notifications=True) -> None:
        """Mark a revision as ready for localization and optionally send notifications."""
        revision.is_ready_for_localization = True
        revision.readied_for_localization = revision.reviewed
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
    pass


class HybridContentManager(WikiContentManager):
    """Content manager for hybrid translation workflow."""
    pass
