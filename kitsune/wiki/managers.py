from django.db import models
from django.db.models import Exists, OuterRef, Q

from kitsune.wiki.permissions import can_delete_documents_or_review_revisions


class DocumentManager(models.Manager):
    def visible(self, user, **kwargs):
        """
        Documents are effectively invisible when they have no approved content,
        and the given user is not a superuser, nor allowed to delete documents or
        review revisions, nor a creator of one of the (yet unapproved) revisions.
        """
        locale = kwargs.get("locale")
        qs = self.filter(**kwargs)

        if not user.is_authenticated:
            # Anonymous users only see documents with approved content.
            return qs.filter(current_revision__isnull=False)

        if not (
            user.is_superuser or can_delete_documents_or_review_revisions(user, locale=locale)
        ):
            # Authenticated users without permission to see documents that
            # have no approved content, can only see those they have created.
            from kitsune.wiki.models import Revision

            rev_created_by_user = Revision.objects.filter(document=OuterRef("pk"), creator=user)
            return qs.filter(Q(current_revision__isnull=False) | Exists(rev_created_by_user))

        return qs

    def get_visible(self, user, **kwargs):
        return self.visible(user, **kwargs).get()


class RevisionManager(models.Manager):
    def visible(self, user, **kwargs):
        """
        Revisions are effectively invisible when their document has no approved content,
        and the given user is not a superuser, nor allowed to delete documents or review
        revisions, nor the creator.
        """
        locale = kwargs.get("document__locale")
        qs = self.filter(**kwargs)

        if not user.is_authenticated:
            # Anonymous users only see revisions of documents with approved content.
            return qs.filter(document__current_revision__isnull=False)

        if not (
            user.is_superuser or can_delete_documents_or_review_revisions(user, locale=locale)
        ):
            # Authenticated users without permission to see documents that
            # have no approved content, can only see the revision they created.
            return qs.filter(Q(document__current_revision__isnull=False) | Q(creator=user))

        return qs

    def get_visible(self, user, **kwargs):
        return self.visible(user, **kwargs).get()
