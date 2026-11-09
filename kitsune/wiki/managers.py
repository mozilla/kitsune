from django.db import models
from django.db.models import Exists, OuterRef, Q

from kitsune.sumo.utils import in_staff_group
from kitsune.wiki.config import DEFAULT_AUDIENCE_SLUG
from kitsune.wiki.permissions import can_delete_documents_or_review_revisions


def effective_group_ids(user, using=None):
    """
    The IDs of the groups that grant the given user access to KB audiences: the user's
    direct groups, plus the company group of each enterprise company the user belongs to
    directly or through a department. Cached on the user; "using" selects the database
    of the first read. The companies come from the per-user cache the support routing shares.
    """
    if not (user and user.is_authenticated):
        return frozenset()

    if not hasattr(user, "_kb_effective_group_ids"):
        # Imported here to break the cycle groups.models -> wiki.parser -> wiki.models -> here.
        from kitsune.groups.models import GroupProfile

        companies = GroupProfile.objects.db_manager(using).cached_enterprise_companies(user)
        user._kb_effective_group_ids = frozenset(
            user.groups.using(using).values_list("id", flat=True)
        ).union(company.group_id for company in companies)
    return user._kb_effective_group_ids


def audience_access(group_ids, prefix=""):
    """
    A condition that is true when the document's original (the document itself when it has
    no parent, otherwise its parent) is assigned a public audience, or an audience with a
    group in "group_ids". The prefix is the ORM path to the document from a related model.
    """
    # Imported here to break the cycle wiki.models -> wiki.managers.
    from kitsune.wiki.models import DocumentAudience

    granted = Q(audience__is_public=True)
    if group_ids:
        granted |= Q(audience__groups__in=group_ids)

    def assigned(document):
        return Exists(DocumentAudience.objects.filter(granted, document=OuterRef(document)))

    return (Q(**{f"{prefix}parent__isnull": True}) & assigned(f"{prefix}pk")) | (
        Q(**{f"{prefix}parent__isnull": False}) & assigned(f"{prefix}parent")
    )


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
        A document is unrestricted for a given user if that user is staff or a superuser,
        or the document's original is assigned an audience that grants the user access
        (see "audience_access"). A translation follows its original's audiences.
        """
        if user and (user.is_superuser or in_staff_group(user)):
            # Staff and superusers are never restricted.
            return self.filter(**kwargs)

        return self.filter(
            audience_access(effective_group_ids(user), self.document_relation_prefix), **kwargs
        )

    def sees_unapproved(self, user, locale=None):
        """
        Whether the given user may see what otherwise only its creators see (documents
        without approved content, held revisions): Staff, superusers, and users allowed to
        delete documents or review revisions in the given locale.
        """
        return bool(user and user.is_authenticated) and (
            user.is_superuser
            or in_staff_group(user)
            or can_delete_documents_or_review_revisions(user, locale=locale)
        )

    def visible(self, user=None, permission_locale=None, sees_unapproved=None, **kwargs):
        """
        Documents are effectively invisible when they are restricted and the given
        user doesn't meet the restrictions, or they have no approved content and the
        given user is not staff, nor a superuser, nor allowed to delete documents or
        review revisions, nor a creator of one of the (yet unapproved) revisions.

        The locale used to check whether the user is allowed to delete documents or
        review revisions is normally taken from the "locale" (or, for related models,
        "<relation>__locale") filter. When the queryset spans multiple locales (for
        example, when filtering revisions by "document__in"), that locale can't be
        inferred, so callers can supply it explicitly via "permission_locale". It only
        affects the permission check, never the filtering. Callers that already know
        the result of "sees_unapproved" for that locale can pass it in.
        """
        prefix = self.document_relation_prefix

        locale = permission_locale or kwargs.get(f"{prefix}locale")

        qs = self.unrestricted(user, **kwargs)

        if not (user and user.is_authenticated):
            # Anonymous users only see documents with approved content.
            return qs.filter(**{f"{prefix}current_revision__isnull": False})

        if sees_unapproved is None:
            sees_unapproved = self.sees_unapproved(user, locale)

        if not sees_unapproved:
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

    def get_held_visibility_condition(self, user, locale=None, sees_unapproved=None):
        """
        Return a condition that hides held revisions (those with a schedule) from the given
        user, unless the user is their creator or may see unapproved content in the locale.
        """
        if sees_unapproved is None:
            sees_unapproved = self.sees_unapproved(user, locale)

        if sees_unapproved:
            # Not Q(), which an OR with another condition drops.
            return Q(pk__isnull=False)

        if user and user.is_authenticated:
            return Q(schedule__isnull=True) | self.get_creator_condition(user)

        return Q(schedule__isnull=True)

    def visible(self, user=None, permission_locale=None, **kwargs):
        """Held revisions are also invisible, as "get_held_visibility_condition" decides."""
        locale = permission_locale or kwargs.get(f"{self.document_relation_prefix}locale")
        sees_unapproved = self.sees_unapproved(user, locale)
        qs = super().visible(
            user, permission_locale=locale, sees_unapproved=sees_unapproved, **kwargs
        )
        return qs.filter(self.get_held_visibility_condition(user, locale, sees_unapproved))


class AudienceManager(models.Manager):
    """The manager for the Audience model."""

    def default(self):
        """
        Return the default knowledge base, where new articles start, creating it if missing.
        For write paths only; read paths check "is_public".
        """
        audience, _created = self.get_or_create(
            slug=DEFAULT_AUDIENCE_SLUG, defaults={"name": "Default", "is_public": True}
        )
        return audience
