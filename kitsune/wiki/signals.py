from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from kitsune.wiki.models import Document


def _rerender_after_commit(document_ids):
    ids = tuple(sorted(set(document_ids)))
    if not ids:
        return

    from kitsune.wiki.tasks import render_document_cascade

    def rerender():
        for document_id in ids:
            render_document_cascade.delay(document_id)

    transaction.on_commit(rerender)


@receiver(
    m2m_changed,
    sender=Document.restrict_to_groups.through,
    dispatch_uid="wiki.render_on_restrict_to_groups_change",
)
def render_on_restrict_to_groups_change(sender, instance, action, reverse, pk_set, **kwargs):
    """
    Trigger a cascade re-render when a document's "restrict_to_groups" changes,
    since the parser uses "restrict_to_groups" to enforce inclusion permission checks.
    Translations inherit their parent's restrict_to_groups, so they must be
    re-rendered as well.

    On the reverse side "instance" is a Group rather than a Document, so the affected
    documents come from "pk_set" instead.
    """
    if reverse:
        if action in ("post_add", "post_remove"):
            document_ids = set(pk_set or ())
        elif action == "pre_clear":
            # Read them now: post_clear can no longer say which documents were unlinked.
            document_ids = set(instance.restricted_documents.values_list("id", flat=True))
        else:
            return
    elif action in ("post_add", "post_remove", "post_clear"):
        document_ids = {instance.pk}
    else:
        return

    translation_ids = Document.objects.filter(parent_id__in=document_ids).values_list(
        "id", flat=True
    )
    _rerender_after_commit(document_ids | set(translation_ids))


@receiver(
    post_save,
    sender=Document,
    dispatch_uid="wiki.reject_obsolete_translations",
)
def reject_obsolete_translations(sender, instance, created, **kwargs):
    """
    When a document is updated, reject any of its unreviewed machine translations
    that may have become obsolete.
    """
    if created:
        # A freshly created document can't lead to obsolete translations.
        return

    from kitsune.wiki.services import HybridTranslationService

    HybridTranslationService().reject_obsolete_translations(instance)


@receiver(
    pre_delete,
    sender=Document,
    dispatch_uid="wiki.rerender_includers_on_delete",
)
def rerender_includers_on_delete(sender, instance, **kwargs):
    """Re-render the documents that included a document being deleted.

    Their stored HTML still contains the deleted content, and the link rows that identify them
    disappear with the cascade — so the includers are captured now and rendered after commit.
    Only *direct* includers are captured; `render_document_cascade` walks the transitive ones
    itself, so the mutation does not carry the whole closure.
    """
    includer_ids = (
        instance.links_to()
        .filter(kind__in=["template", "include"])
        .values_list("linked_from_id", flat=True)
    )
    _rerender_after_commit(includer_ids)


@receiver(
    pre_delete,
    sender=Group,
    dispatch_uid="wiki.rerender_restricted_documents_on_group_delete",
)
def rerender_restricted_documents_on_group_delete(sender, instance, **kwargs):
    """Capture restricted families before deleting the group widens their access."""
    restricted_ids = instance.restricted_documents.values_list("id", flat=True)
    originals = {
        parent_id or document_id
        for parent_id, document_id in Document.objects.filter(pk__in=restricted_ids).values_list(
            "parent_id", "id"
        )
    }
    affected_ids = Document.objects.filter(
        Q(pk__in=originals) | Q(parent_id__in=originals)
    ).values_list("id", flat=True)
    _rerender_after_commit(affected_ids)
