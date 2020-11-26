from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from kitsune.search.v2.es7_utils import (
    index_object,
    delete_object,
    index_objects_bulk,
    remove_from_field,
)
from kitsune.questions.models import Question, QuestionVote, Answer, AnswerVote
from taggit.models import Tag


@receiver(post_save, sender=Question)
@receiver(m2m_changed, sender=Question.tags.through)
def handle_question_save(instance, **kwargs):
    if getattr(kwargs, "action", "").startswith("pre_"):
        # skip pre m2m_changed signals
        return
    if settings.ES_LIVE_INDEXING:
        index_object.delay("QuestionDocument", instance.pk)
        index_objects_bulk.delay(
            "AnswerDocument", list(instance.answers.values_list("pk", flat=True))
        )


@receiver(post_delete, sender=Question)
def handle_question_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        delete_object.delay("QuestionDocument", instance.pk)


@receiver(post_delete, sender=Answer)
def handle_answer_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        delete_object.delay("AnswerDocument", instance.pk)
        index_object.delay("QuestionDocument", instance.question_id)


@receiver(post_delete, sender=Tag)
def handle_tag_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        remove_from_field.delay("QuestionDocument", "question_tag_ids", instance.pk)


@receiver(post_delete, sender=QuestionVote)
def handle_question_vote_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        index_object.delay("QuestionDocument", instance.question_id)
        index_objects_bulk.delay(
            "AnswerDocument", list(instance.question.answers.values_list("pk", flat=True))
        )


@receiver(post_save, sender=AnswerVote)
def handle_answer_vote_save(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        index_object.delay("AnswerDocument", instance.answer_id)


@receiver(post_delete, sender=AnswerVote)
def handle_answer_vote_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        index_object.delay("AnswerDocument", instance.answer_id)
