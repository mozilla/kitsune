from unittest.mock import patch

from kitsune.questions.tests import (
    AnswerFactory,
    AnswerVoteFactory,
    QuestionFactory,
    QuestionVoteFactory,
)
from kitsune.search.documents import AnswerDocument, QuestionDocument
from kitsune.sumo.tests import TestCase
from kitsune.tags.tests import TagFactory


class QuestionDocumentTests(TestCase):
    def test_annotation_has_correct_counts(self):
        question = QuestionFactory()
        AnswerFactory(question=question, content="answer 1")
        [f(question=question) for f in [QuestionVoteFactory] * 4]

        document = QuestionDocument.prepare(question)
        self.assertEqual(document.question_num_votes, 4)

        annotated_question = QuestionDocument.get_queryset().get(id=question.id)

        document = QuestionDocument.prepare(annotated_question)
        self.assertEqual(document.question_num_votes, 4)

    def test_tag_slugs_excludes_archived_tags(self):
        active_tag = TagFactory(is_archived=False)
        archived_tag = TagFactory(is_archived=True)
        question = QuestionFactory()
        question.tags.add(active_tag)
        question.tags.add(archived_tag)

        document = QuestionDocument.prepare(question)
        self.assertIn(active_tag.slug, document.question_tag_slugs)
        self.assertNotIn(archived_tag.slug, document.question_tag_slugs)

    def test_has_answers_false_when_no_answers(self):
        question = QuestionFactory()
        document = QuestionDocument.prepare(question)
        self.assertFalse(document.question_has_answers)

    def test_has_answers_true_when_answered(self):
        question = QuestionFactory()
        AnswerFactory(question=question)
        question.refresh_from_db()
        document = QuestionDocument.prepare(question)
        self.assertTrue(document.question_has_answers)

    def test_last_answer_is_by_creator_none_when_no_answers(self):
        question = QuestionFactory()
        document = QuestionDocument.prepare(question)
        self.assertIsNone(document.question_last_answer_is_by_creator)

    def test_last_answer_is_by_creator_true_when_creator_answered(self):
        question = QuestionFactory()
        AnswerFactory(question=question, creator=question.creator)
        question.refresh_from_db()
        document = QuestionDocument.prepare(question)
        self.assertTrue(document.question_last_answer_is_by_creator)

    def test_last_answer_is_by_creator_false_when_other_user_answered(self):
        question = QuestionFactory()
        AnswerFactory(question=question)
        question.refresh_from_db()
        document = QuestionDocument.prepare(question)
        self.assertFalse(document.question_last_answer_is_by_creator)


class AnswerDocumentTests(TestCase):
    def test_document_has_correct_counts(self):
        answer = AnswerFactory()
        [f(question=answer.question) for f in [QuestionVoteFactory] * 4]
        [f(helpful=False, answer=answer) for f in [AnswerVoteFactory] * 3]
        [f(helpful=True, answer=answer) for f in [AnswerVoteFactory] * 2]

        document = AnswerDocument.prepare(answer)
        self.assertEqual(document.question_num_votes, 4)
        self.assertEqual(document.num_unhelpful_votes, 3)
        self.assertEqual(document.num_helpful_votes, 2)

        annotated_answer = AnswerDocument.get_queryset().get(id=answer.id)

        document = AnswerDocument.prepare(annotated_answer)
        self.assertEqual(document.question_num_votes, 4)
        self.assertEqual(document.num_unhelpful_votes, 3)
        self.assertEqual(document.num_helpful_votes, 2)

    def test_id_wont_clash_with_question_id(self):
        answer = AnswerFactory()
        document = AnswerDocument.prepare(answer)
        self.assertNotEqual(answer.id, document.meta.id)
        self.assertIn(str(answer.id), str(document.meta.id))

    @patch("kitsune.search.documents.SumoDocument.get")
    def test_get_works_with_unprefixed_ids(self, mock_get):
        AnswerDocument.get(123)
        mock_get.assert_called_with("a_123")

    @patch("kitsune.search.documents.SumoDocument.get")
    def test_get_works_with_prefixed_ids(self, mock_get):
        AnswerDocument.get("a_123")
        mock_get.assert_called_with("a_123")
