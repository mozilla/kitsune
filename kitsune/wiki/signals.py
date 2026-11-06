from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete
from django.dispatch import receiver

from kitsune.wiki.models import Audience, Document
from kitsune.wiki.utils import retire_public_kb_listing


def _rerender_after_commit(document_ids):
    ids = tuple(sorted(set(document_ids)))
    if not ids:
        return

    from kitsune.wiki.tasks import render_document_cascade

    def rerender():
        for document_id in ids:
            render_document_cascade.delay(document_id)

    transaction.on_commit(rerender)


def _follow_access_change(document_ids, *, sync_redirects):
    """
    Trigger a cascade re-render of the documents whose access changed, since the parser
    uses access to enforce inclusion permission checks. Translations inherit their parent's
    audiences, so they must be re-rendered as well. The families' cached anonymous pages are
    cleared on commit, once other requests can see the change. Redirect stubs copy their
    target's audiences, so they follow assignment changes at once when "sync_redirects" is set.
    """
    originals = {
        document.original
        for document in Document.objects.filter(id__in=document_ids).select_related("parent")
    }
    if sync_redirects:
        for original in originals:
            original.sync_redirect_audiences()

    translation_ids = Document.objects.filter(parent_id__in=document_ids).values_list(
        "id", flat=True
    )
    _rerender_after_commit(set(document_ids) | set(translation_ids))

    def clear_family_page_caches():
        for original in originals:
            original.clear_family_page_cache()

    transaction.on_commit(clear_family_page_caches)


@receiver(
    m2m_changed,
    sender=Document.audiences.through,
    dispatch_uid="wiki.render_on_audiences_change",
)
def render_on_audiences_change(sender, instance, action, reverse, pk_set, **kwargs):
    """
    Follow up on a change to a document's audiences.

    On the reverse side "instance" is an Audience rather than a Document, so the affected
    documents come from "pk_set" instead.
    """
    if reverse:
        if action in ("post_add", "post_remove"):
            document_ids = set(pk_set or ())
        elif action == "pre_clear":
            # Read them now: post_clear can no longer say which documents were unlinked.
            instance._cleared_document_ids = set(instance.documents.values_list("id", flat=True))
            return
        elif action == "post_clear":
            document_ids = instance.__dict__.pop("_cleared_document_ids", set())
        else:
            return
    elif action in ("post_add", "post_remove", "post_clear"):
        document_ids = {instance.pk}
    else:
        return

    _follow_access_change(document_ids, sync_redirects=True)


@receiver(
    post_save,
    sender=Audience,
    dispatch_uid="wiki.render_on_audience_visibility_change",
)
def render_on_audience_visibility_change(sender, instance, **kwargs):
    """A knowledge base turning public or private changes access to every article in it."""
    if getattr(instance, "visibility_changed", False):
        _follow_access_change(
            set(instance.documents.values_list("id", flat=True)), sync_redirects=False
        )


@receiver(
    [post_save, post_delete],
    sender=Audience,
    dispatch_uid="wiki.clear_public_kb_listing_on_audience_change",
)
def clear_public_kb_listing(sender, **kwargs):
    """Retire the menu's cached public knowledge bases once the change is visible to others."""
    transaction.on_commit(retire_public_kb_listing)


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
