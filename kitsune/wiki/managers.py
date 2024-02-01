from django.db import models
from django.db.models import Exists, OuterRef, Q

from kitsune.wiki.permissions import can_delete_documents_or_review_revisions


class VisibilityManager(models.Manager):
    """Abstract base class for the Document and Revision Managers."""

    # For managers of models related to documents, provide the name of the model attribute
    # that provides the related document. For example, for the manager of revisions, this
    # should be "document".
    document_relation: str | None = None

    @property
    def document_relation_prefix(self):
        """Provides ORM prefix for the document relation."""
        return f"{self.document_relation}__" if self.document_relation else ""

    def get_creator_condition(self, user):
        """
        Return a conditional (e.g., a Q or Exists object) that is only true
        when the given user is the creator of this document or revision.
        """
        raise NotImplementedError

    def unrestricted(self, user=None, **kwargs):
        """
        A document is unrestricted for a given user if that user is staff or a
        superuser, or the document is not restricted to one or more groups, or
        when the user is a member of at least one of the groups to which it's
        restricted. A translation (i.e., a document with a parent), follows its
        parent's restrictions.
        """
        if user and (user.is_staff or user.is_superuser):
            # Staff and superusers are never restricted.
            return self.filter(**kwargs)

        prefix = self.document_relation_prefix

        # Authenticated users might have one or more groups to match against.
        check_for_group_match = user and user.is_authenticated

        def unrestricted_condition(parent_prefix=""):
            """
            Create the unrestricted condition for either the document or
            the document's parent.
            """
            restrict_to_groups = f"{prefix}{parent_prefix}restrict_to_groups"

            parent_condition = Q(**{f"{prefix}parent__isnull": not bool(parent_prefix)})
            not_restricted = Q(**{f"{restrict_to_groups}__isnull": True})

            if not check_for_group_match:
                return parent_condition & not_restricted

            group_condition_fulfilled = Q(**{f"{restrict_to_groups}__in": user.groups.all()})

            return parent_condition & (not_restricted | group_condition_fulfilled)

        qs = self.filter(
            unrestricted_condition() | unrestricted_condition("parent__"),
            **kwargs,
        )

        if check_for_group_match:
            # If we're looking for a group match, we might get duplicate rows,
            # because a single document might have multiple group matches if
            # the user is a member of multiple groups.
            qs = qs.distinct()

        return qs

    def visible(self, user=None, **kwargs):
        """
        Documents are effectively invisible when they are restricted and the given
        user doesn't meet the restrictions, or they have no approved content and the
        given user is not staff, nor a superuser, nor allowed to delete documents or
        review revisions, nor a creator of one of the (yet unapproved) revisions.
        """
        prefix = self.document_relation_prefix

        locale = kwargs.get(f"{prefix}locale")

        qs = self.unrestricted(user, **kwargs)

        if not (user and user.is_authenticated):
            # Anonymous users only see documents with approved content.
            return qs.filter(**{f"{prefix}current_revision__isnull": False})

        if not (
            user.is_staff
            or user.is_superuser
            or can_delete_documents_or_review_revisions(user, locale=locale)
        ):
            # Authenticated users without permission to see documents that
            # have no approved content, can only see those they have created.
            return qs.filter(
                Q(**{f"{prefix}current_revision__isnull": False})
                | self.get_creator_condition(user)
            )

        return qs

    def get_visible(self, user=None, **kwargs):
        """
        Returns either a single Document object, identified by the keyword arguments
        and visible to the given user, or else raises either a DoesNotExist or
        MultipleObjectsReturned exception.
        """
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
