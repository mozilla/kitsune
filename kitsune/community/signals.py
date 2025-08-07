from django.contrib.contenttypes.models import ContentType
from django.db.models import Max, QuerySet
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from kitsune.community.models import DeletedContribution
from kitsune.questions.models import Answer
from kitsune.wiki.models import Document, Revision


def skip_on_user_deletion(user, origin):
    """
    Within the context of a pre or post-delete event, returns whether or
    not the deletion of the given user is at least part of the origin of
    the event.
    """
    if not origin:
        return False

    if isinstance(origin, QuerySet):
        return origin.filter(pk=user.pk).exists()

    # The origin is a Django model instance.
    return user == origin


@receiver(
    pre_delete,
    sender=Answer,
    dispatch_uid="community.record_deleted_answer_contributions",
)
def record_deleted_answer_contributions(sender, instance, origin, **kwargs):
    """
    When an answer is about to be deleted, record the contribution of its creator.
    """
    question = instance.question

    if not (
        instance.is_spam
        or (not instance.creator.is_active)
        or (instance.creator == question.creator)
        or instance.creator.profile.is_system_account
        or skip_on_user_deletion(instance.creator, origin)
    ):
        dc = DeletedContribution.objects.create(
            content_type=ContentType.objects.get_for_model(Answer),
            contributor=instance.creator,
            contribution_timestamp=instance.created,
            locale=question.locale,
            metadata={
                "content": instance.content,
                "question_title": question.title,
                "is_solution": instance.id == question.solution_id,
            },
        )
        if question.product:
            dc.products.set([question.product])


@receiver(
    pre_delete,
    sender=Revision,
    dispatch_uid="community.record_deleted_revision_contribution",
)
def record_deleted_revision_contribution(sender, instance, origin, **kwargs):
    """
    When a revision is about to be deleted, record the contribution of its creator.
    """
    if (
        instance.creator.is_active
        and not instance.creator.profile.is_system_account
        and not skip_on_user_deletion(instance.creator, origin)
    ):
        dc = DeletedContribution.objects.create(
            content_type=ContentType.objects.get_for_model(Revision),
            contributor=instance.creator,
            contribution_timestamp=instance.created,
            locale=instance.document.locale,
            metadata={
                "is_approved": instance.is_approved,
                "document_title": instance.document.title,
            },
        )
        dc.products.set(instance.document.original.products.all())


@receiver(
    pre_delete,
    sender=Document,
    dispatch_uid="community.record_deleted_document_contributions",
)
def record_deleted_document_contributions(sender, instance, origin, **kwargs):
    """
    When a document is about to be deleted, record a contribution for each of its contributors.
    """
    for contributor in instance.contributors.all():
        if (
            contributor.is_active
            and not contributor.profile.is_system_account
            and not skip_on_user_deletion(contributor, origin)
        ):
            last_contribution_timestamp = instance.revisions.filter(
                is_approved=True, creator=contributor
            ).aggregate(last_created=Max("created"))["last_created"]

            dc = DeletedContribution.objects.create(
                content_type=ContentType.objects.get_for_model(Document),
                contributor=contributor,
                contribution_timestamp=last_contribution_timestamp,
                locale=instance.locale,
                metadata={"title": instance.title},
            )
            dc.products.set(instance.original.products.all())
