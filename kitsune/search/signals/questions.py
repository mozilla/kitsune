from django.db.models.signals import m2m_changed, post_delete, post_save

from kitsune.questions.models import Answer, AnswerVote, Question, QuestionVote
from kitsune.search.decorators import search_receiver
from kitsune.search.es_utils import (
    delete_object,
    index_object,
    index_objects_bulk,
    remove_from_field,
)
from kitsune.tags.models import SumoTag


@search_receiver(post_save, Question)
@search_receiver(m2m_changed, Question.tags.through)
def handle_question_save(instance, **kwargs):
    if not isinstance(instance, Question):
        return
    index_object.delay("QuestionDocument", instance.pk)
    index_objects_bulk.delay("AnswerDocument", list(instance.answers.values_list("pk", flat=True)))


@search_receiver(post_delete, Question)
def handle_question_delete(instance, **kwargs):
    delete_object.delay("QuestionDocument", instance.pk)


@search_receiver(post_delete, Answer)
def handle_answer_delete(instance, **kwargs):
    delete_object.delay("AnswerDocument", instance.pk)
    index_object.delay("QuestionDocument", instance.question_id)


@search_receiver(post_delete, SumoTag)
def handle_tag_delete(instance, **kwargs):
    remove_from_field.delay("QuestionDocument", "question_tag_ids", instance.pk)


@search_receiver(post_delete, QuestionVote)
def handle_question_vote_delete(instance, **kwargs):
    index_object.delay("QuestionDocument", instance.question_id)
    index_objects_bulk.delay(
        "AnswerDocument", list(instance.question.answers.values_list("pk", flat=True))
    )


@search_receiver(post_save, AnswerVote)
def handle_answer_vote_save(instance, **kwargs):
    index_object.delay("AnswerDocument", instance.answer_id)


@search_receiver(post_delete, AnswerVote)
def handle_answer_vote_delete(instance, **kwargs):
    index_object.delay("AnswerDocument", instance.answer_id)
