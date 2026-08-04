"""Freshness triggers for retrieval.

Every receiver defers its queueing to ``transaction.on_commit``, so a rolled-back mutation
never schedules work, and every receiver that needs to know *what changed* reads it before the
rows disappear — a ``post_clear`` or post-cascade handler cannot recover what was unlinked.

Access changes are handled here as ordinary freshness transitions rather than by a separate
security workflow (ADR 0006). Under the public-only policy, restricting a document makes it
ineligible and the sync core evicts it; widening access makes it eligible and it is indexed.
"""

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from kitsune.products.models import Product, Topic
from kitsune.retrieval.index import ChunkIdentity
from kitsune.retrieval.tasks import enqueue_document_delete, enqueue_document_sync
from kitsune.wiki.models import Document

CONTENT_TYPE = "kb"


def _refresh_families(document_ids) -> None:
    """Queue a sync for every member of every affected translation family, after commit.

    Refreshing whole families is affordable because the hash gate makes unchanged members
    provider-free, and it is necessary because translations inherit products, topics, category
    and access from their original.
    """
    if not settings.RETRIEVAL_LIVE_INDEXING:
        return

    seeds = set(document_ids)
    if not seeds:
        return
    originals = {
        parent_id or own_id
        for parent_id, own_id in Document.objects.filter(pk__in=seeds).values_list(
            "parent_id", "id"
        )
    }
    members = sorted(
        Document.objects.filter(Q(pk__in=originals) | Q(parent_id__in=originals)).values_list(
            "id", flat=True
        )
    )

    def queue_family():
        for member in members:
            enqueue_document_sync(member)

    transaction.on_commit(queue_family)


def _affected_documents(instance, action, reverse, pk_set, *, reverse_accessor) -> list[int]:
    if not settings.RETRIEVAL_LIVE_INDEXING:
        return []
    if not reverse:
        return [instance.pk] if action in ("post_add", "post_remove", "pre_clear") else []
    if action in ("post_add", "post_remove"):
        return list(pk_set or ())
    if action == "pre_clear":
        # Read the links now: post_clear cannot say which documents were unlinked.
        return list(getattr(instance, reverse_accessor).values_list("id", flat=True))
    return []


@receiver(post_save, sender=Document, dispatch_uid="retrieval.document_saved")
def document_saved(sender, instance, **kwargs):
    _refresh_families([instance.pk])


@receiver(
    m2m_changed,
    sender=Document.products.through,
    dispatch_uid="retrieval.document_products_changed",
)
@receiver(
    m2m_changed, sender=Document.topics.through, dispatch_uid="retrieval.document_topics_changed"
)
def taxonomy_changed(sender, instance, action, reverse, pk_set, **kwargs):
    _refresh_families(
        _affected_documents(instance, action, reverse, pk_set, reverse_accessor="document_set")
    )


@receiver(pre_delete, sender=Product, dispatch_uid="retrieval.product_deleted")
@receiver(pre_delete, sender=Topic, dispatch_uid="retrieval.topic_deleted")
def taxonomy_deleted(sender, instance, **kwargs):
    # Capture before the cascade removes the join rows.
    _refresh_families(instance.document_set.values_list("id", flat=True))


@receiver(
    m2m_changed,
    sender=Document.restrict_to_groups.through,
    dispatch_uid="retrieval.document_restrictions_changed",
)
def restrictions_changed(sender, instance, action, reverse, pk_set, **kwargs):
    _refresh_families(
        _affected_documents(
            instance, action, reverse, pk_set, reverse_accessor="restricted_documents"
        )
    )


@receiver(pre_delete, sender=Group, dispatch_uid="retrieval.group_deleted")
def group_deleted(sender, instance, **kwargs):
    _refresh_families(instance.restricted_documents.values_list("id", flat=True))


@receiver(pre_delete, sender=Document, dispatch_uid="retrieval.document_deleted")
def document_deleted(sender, instance, **kwargs):
    """Evict a deleted document, capturing its identity while the row still exists.

    A deleted row cannot report its locale, and the identity is what scopes the eviction, so
    it has to be read here rather than after the delete.
    """
    identity = ChunkIdentity(
        content_type=CONTENT_TYPE, object_id=str(instance.pk), locale=instance.locale
    )
    transaction.on_commit(lambda: enqueue_document_delete(identity))
