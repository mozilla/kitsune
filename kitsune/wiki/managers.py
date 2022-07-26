from django.db import models
from django.db.models import Exists, OuterRef, Q

from kitsune.wiki.permissions import can_delete_documents_or_review_revisions


class VisibilityManager(models.Manager):
    """Abstract base class for the Document and Revision Managers."""

    # For managers of models related to documents, provide the name of the model attribute
    # that provides the related document. For example, for the manager of revisions, this
    # should be "document".
    document_relation = None

    def get_creator_condition(self, user):
        """
        Return a conditional (e.g., a Q or Exists object) that is only true
        when the given user is the creator of this document or revision.
        """
        raise NotImplementedError

    def visible(self, user, **kwargs):
        """
        Documents are effectively invisible when they have no approved content,
        and the given user is not a superuser, nor allowed to delete documents or
        review revisions, nor a creator of one of the (yet unapproved) revisions.
        """
        prefix = f"{self.document_relation}__" if self.document_relation else ""

        locale = kwargs.get(f"{prefix}locale")

        qs = self.filter(**kwargs)

        if not user.is_authenticated:
            # Anonymous users only see documents with approved content.
            return qs.filter(**{f"{prefix}current_revision__isnull": False})

        if not (
            user.is_superuser or can_delete_documents_or_review_revisions(user, locale=locale)
        ):
            # Authenticated users without permission to see documents that
            # have no approved content, can only see those they have created.
            return qs.filter(
                Q(**{f"{prefix}current_revision__isnull": False})
                | self.get_creator_condition(user)
            )

        return qs

    def get_visible(self, user, **kwargs):
        return self.visible(user, **kwargs).get()


class DocumentManager(VisibilityManager):
    """The manager for the Document model."""

    def get_creator_condition(self, user):
        from kitsune.wiki.models import Revision

        return Exists(Revision.objects.filter(document=OuterRef("pk"), creator=user))


class RevisionManager(VisibilityManager):
    """The manager for the Revision model."""

    document_relation = "document"

    def get_creator_condition(self, user):
        return Q(creator=user)
