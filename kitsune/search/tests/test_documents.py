from unittest.mock import patch
from kitsune.sumo.tests import TestCase
from kitsune.questions.tests import (
    QuestionFactory,
    QuestionVoteFactory,
    AnswerFactory,
    AnswerVoteFactory,
)
from kitsune.search.documents import QuestionDocument, AnswerDocument


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
