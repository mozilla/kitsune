from datetime import datetime
from typing import Any

from django.db import models

from kitsune.users.models import Profile
from kitsune.wiki.events import (
    ApprovedOrReadyUnion,
    EditDocumentEvent,
    ReadyRevisionEvent,
    ReviewableRevisionInLocaleEvent,
)
from kitsune.wiki.models import Document, DraftRevision, Revision


class NotificationType(models.TextChoices):
    """Types of notifications that can be fired by content managers."""

    CONTENT_CREATION = "content_creation", "Content Creation"
    TRANSLATION_WORKFLOW = "translation_workflow", "Translation Workflow"
    READY_FOR_L10N = "ready_for_l10n", "Ready for Localization"


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

    def publish_revision(self, revision: Revision, user, send_notifications=True) -> Revision:
        """Publish (approve) a revision.

        Args:
            revision: The revision to publish
            user: The user publishing the revision
            send_notifications: Whether to send content creation notifications
        """
        revision.is_approved = True
        revision.reviewed = datetime.now()
        revision.reviewer = user
        revision.save()

        if send_notifications:
            exclude_users = [user] if user else []
            self.fire_notifications(revision, [NotificationType.CONTENT_CREATION], exclude_users)
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

    def mark_ready_for_localization(
        self, revision: Revision, user=None, send_notifications=True
    ) -> None:
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
        target_locale = data.pop('target_locale', None)
        translated_content = data.pop('translated_content', None)

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

            data['created'] = datetime.now()

        return super().create_revision(data, document, Profile.get_sumo_bot(), based_on_id, base_rev, send_notifications)

    def publish_revision(self, revision: Revision, user=None, send_notifications=True) -> Revision:
        """Publish (approve) a revision using the sumo bot.

        Args:
            revision: The revision to publish
            send_notifications: Whether to send content creation notifications
        """
        user = user or Profile.get_sumo_bot()
        return super().publish_revision(revision, user, send_notifications)


class HybridContentManager(WikiContentManager):
    """Content manager for hybrid translation workflow."""

    pass
