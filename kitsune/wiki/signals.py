from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from kitsune.wiki import tasks
from kitsune.wiki.models import Document


def cascade_render_on_commit(document_ids):
    """
    Queue a cascade re-render of the given documents and their translations, once the
    current transaction commits. Dispatching any earlier lets a worker pick up the task
    and render against restrictions that haven't been committed yet.
    """
    if not document_ids:
        return

    translation_ids = Document.objects.filter(parent_id__in=document_ids).values_list(
        "id", flat=True
    )
    render_ids = sorted(set(document_ids) | set(translation_ids))

    def render_documents():
        for document_id in render_ids:
            # Resolved through the module so that tests can patch the task.
            tasks.render_document_cascade.delay(document_id)

    transaction.on_commit(render_documents)


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

    cascade_render_on_commit(document_ids)


@receiver(
    pre_delete,
    sender=Group,
    dispatch_uid="wiki.render_on_restricting_group_deletion",
)
def render_on_restricting_group_deletion(sender, instance, **kwargs):
    """
    Trigger a cascade re-render of the documents a group restricts when that group is
    deleted. Django's delete collector drops the "restrict_to_groups" rows as a fast
    delete without sending "m2m_changed", so those documents would otherwise keep HTML
    rendered against restrictions that no longer apply.

    This reads the documents in "pre_delete" because by "post_delete" the rows linking
    them to the group are already gone. It hangs off a signal rather than Group.delete()
    so that bulk deletes are covered too.
    """
    cascade_render_on_commit(set(instance.restricted_documents.values_list("id", flat=True)))


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
