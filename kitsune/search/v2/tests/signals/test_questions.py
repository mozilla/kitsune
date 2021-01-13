from unittest.mock import patch, call
from kitsune.search.v2.tests import Elastic7TestCase
from kitsune.questions.tests import (
    QuestionFactory,
    AnswerFactory,
    QuestionVoteFactory,
    AnswerVoteFactory,
)
from kitsune.wiki.tests import DocumentFactory
from kitsune.tags.tests import TagFactory

from kitsune.search.v2.documents import QuestionDocument, AnswerDocument
from elasticsearch7.exceptions import NotFoundError


class QuestionDocumentSignalsTests(Elastic7TestCase):
    def setUp(self):
        self.question = QuestionFactory()
        self.question_id = self.question.id

    def get_doc(self):
        return QuestionDocument.get(self.question_id)

    def test_question_save(self):
        self.question.title = "foobar"
        self.question.save()

        self.assertEqual(self.get_doc().question_title["en-US"], "foobar")

    def test_answer_save(self):
        AnswerFactory(question=self.question, content="foobar")

        self.assertIn("foobar", self.get_doc().answer_content["en-US"])

    def test_vote_save(self):
        QuestionVoteFactory(question=self.question)

        self.assertEqual(self.get_doc().question_num_votes, 1)

    def test_tags_change(self):
        tag = TagFactory()
        self.question.tags.add(tag)

        self.assertIn(tag.id, self.get_doc().question_tag_ids)

        self.question.tags.remove(tag)

        self.assertNotIn(tag.id, self.get_doc().question_tag_ids)

    def test_question_delete(self):
        self.question.delete()

        with self.assertRaises(NotFoundError):
            self.get_doc()

    def test_answer_delete(self):
        answer = AnswerFactory(question=self.question, content="foobar")
        answer.delete()

        self.assertNotIn("en-US", self.get_doc().answer_content)

    def test_vote_delete(self):
        vote = QuestionVoteFactory(question=self.question)
        vote.delete()

        self.assertEqual(self.get_doc().question_num_votes, 0)

    def test_tag_delete(self):
        tag = TagFactory()
        self.question.tags.add(tag)
        tag.delete()

        self.assertEqual(self.get_doc().question_tag_ids, [])

    @patch("kitsune.search.v2.signals.questions.index_object.delay")
    def test_kb_tag(self, mock_index_object):
        # the tag m2m relation is shared across all models which use it
        # so will trigger signals on all models which use it, but we don't
        # want this to happen
        mock_index_object.reset_mock()
        document = DocumentFactory(tags=["foobar"])
        self.assertNotIn(call("QuestionDocument", document.id), mock_index_object.call_args_list)


class AnswerDocumentSignalsTests(Elastic7TestCase):
    def setUp(self):
        self.answer = AnswerFactory()
        self.answer_id = self.answer.id

    def get_doc(self):
        return AnswerDocument.get(self.answer_id)

    def test_answer_save(self):
        self.answer.content = "foobar"
        self.answer.save()

        self.assertEqual(self.get_doc().content["en-US"], "foobar")

    def test_vote_save(self):
        AnswerVoteFactory(answer=self.answer, helpful=True)

        self.assertEqual(self.get_doc().num_helpful_votes, 1)

    def test_question_save(self):
        question = self.answer.question
        question.title = "barfoo"
        question.save()

        self.assertEqual(self.get_doc().question_title["en-US"], "barfoo")

    def test_question_vote_save(self):
        QuestionVoteFactory(question=self.answer.question)

        self.assertEqual(self.get_doc().question_num_votes, 1)

    def test_question_tags_change(self):
        question = self.answer.question
        tag = TagFactory()
        question.tags.add(tag)

        self.assertIn(tag.id, self.get_doc().question_tag_ids)

        question.tags.remove(tag)

        self.assertNotIn(tag.id, self.get_doc().question_tag_ids)

    def test_answer_delete(self):
        self.answer.delete()

        with self.assertRaises(NotFoundError):
            self.get_doc()

    def test_vote_delete(self):
        vote = AnswerVoteFactory(answer=self.answer, helpful=True)
        vote.delete()

        self.assertEqual(self.get_doc().num_helpful_votes, 0)

    def test_question_delete(self):
        self.answer.question.delete()

        with self.assertRaises(NotFoundError):
            self.get_doc()

    def test_question_vote_delete(self):
        vote = QuestionVoteFactory(question=self.answer.question)
        vote.delete()

        self.assertEqual(self.get_doc().question_num_votes, 0)

    def test_question_tag_delete(self):
        tag = TagFactory()
        self.answer.question.tags.add(tag)
        tag.delete()

        self.assertEqual(self.get_doc().question_tag_ids, [])
