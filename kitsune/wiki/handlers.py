from django.conf import settings
from django.contrib.auth.models import Group, User

from kitsune.sumo.anonymous import AnonymousIdentity
from kitsune.users.handlers import UserDeletionListener
from kitsune.users.models import Profile
from kitsune.wiki.models import Document, HelpfulVote, Revision


class DocumentListener(UserDeletionListener):
    """Listener for document-related tasks."""

    def on_user_deletion(self, user: User) -> None:
        """Handle the deletion of a user.

        - Replace the user as a document contributor with content group members
          if they were the only contributor.
        - Anonymize the user's revision votes.
        - Delete the user's non-approved revisions.
        - Replace the user as creator/reviewer of approved revisions with the SUMO bot.
        """
        sumo_bot = Profile.get_sumo_bot()
        content_group = Group.objects.get(name=settings.SUMO_CONTENT_GROUP)

        # Handle approved revisions first to avoid cascade deletion issues
        Revision.objects.filter(creator=user, is_approved=True).update(creator=sumo_bot)
        # Update reviewer field
        Revision.objects.filter(reviewer=user).update(reviewer=sumo_bot)
        # Update readied_for_localization_by field separately
        Revision.objects.filter(readied_for_localization_by=user).update(
            readied_for_localization_by=sumo_bot
        )

        documents = Document.objects.filter(contributors=user)
        for document in documents:
            if not document.contributors.exclude(id=user.id).exists():
                document.contributors.add(*content_group.user_set.all())
            document.contributors.remove(user)

        HelpfulVote.objects.filter(creator=user).update(
            creator=None, anonymous_id=AnonymousIdentity().anonymous_id
        )

        Document.objects.filter(
            revisions__creator=user,
            current_revision__isnull=True,
        ).exclude(revisions__creator__in=User.objects.exclude(id=user.id)).delete()
        Revision.objects.filter(creator=user, is_approved=False).delete()
