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
        # The based-on value of localized revisions is essential, so if the based-on revision
        # is un-approved and created by the user to be deleted, we should ensure that it is
        # retained by re-assigning it to the "sumo_bot". It's very rare that the based-on
        # revision of a localized revision is un-approved (less than 1%), but it is possible.
        # The based-on value of non-localized revisions is not nearly as important, so in those
        # cases, we can simply let the cascade behavior set the based-on value to NULL.
        Revision.objects.filter(
            id__in=(
                Revision.objects.exclude(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
                .filter(
                    based_on__creator=user,
                    based_on__is_approved=False,
                    # This locale check ensures only legitimate based-on references.
                    based_on__document__locale=settings.WIKI_DEFAULT_LANGUAGE,
                )
                .values_list("based_on__id", flat=True)
            )
        ).update(creator=sumo_bot)

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
