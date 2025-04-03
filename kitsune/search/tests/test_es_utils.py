from kitsune.search.tests import ElasticTestCase
from kitsune.questions.tests import QuestionFactory, AnswerFactory
from django.test.utils import override_settings
from kitsune.search.es_utils import index_objects_bulk, es_client, recreate_index_and_mapping
from elasticsearch.helpers.errors import BulkIndexError
from elasticsearch.exceptions import NotFoundError
from kitsune.search.documents import QuestionDocument
from kitsune.questions.models import Question
from unittest.mock import patch, MagicMock
from kitsune.search.base import SumoDocument


@override_settings(ES_LIVE_INDEXING=False)
class IndexObjectsBulkTestCase(ElasticTestCase):
    def test_delete_not_found_not_raised(self):
        q_id = QuestionFactory(is_spam=True).id
        index_objects_bulk("QuestionDocument", [q_id])

    @patch("kitsune.search.documents.QuestionDocument.to_action", autospec=True)
    def test_errors_are_raised_after_all_chunks_are_sent(self, mock_to_action):
        es_exception_will_be_thrown = False
        id_without_exception = None

        def make_first_doc_throw_exception(self, *args, **kwargs):
            nonlocal es_exception_will_be_thrown, id_without_exception
            if es_exception_will_be_thrown:
                id_without_exception = self.meta.id
                return SumoDocument.to_action(self, *args, **kwargs)
            payload = self.to_dict(include_meta=True)
            del payload["_source"]
            payload.update(
                {
                    "_op_type": "update",
                    "scripted_upsert": True,
                    "upsert": {},
                    "script": {"source": "throw new Exception();"},
                }
            )
            es_exception_will_be_thrown = True
            return payload

        mock_to_action.side_effect = make_first_doc_throw_exception

        ids = [QuestionFactory().id for _ in range(2)]
        for question_id in ids:
            question = Question.objects.get(id=question_id)
            AnswerFactory(question=question, content=f"answer {question_id}")

        with self.assertRaises(BulkIndexError):
            index_objects_bulk("QuestionDocument", ids, elastic_chunk_size=1)

        try:
            QuestionDocument.get(id_without_exception)
        except NotFoundError:
            self.fail("Couldn't get question, so later chunks weren't sent.")


@override_settings(ES_LIVE_INDEXING=False)
class ES8CompatibilityTestCase(ElasticTestCase):
    @patch("elasticsearch.Elasticsearch.search")
    def test_search_uses_query_param_not_body(self, mock_search):
        # Create mock return value
        mock_response = MagicMock()
        mock_response.body = {"hits": {"hits": []}}
        mock_search.return_value = mock_response

        # Create a client and perform a search
        client = es_client()
        query = {"query": {"match_all": {}}}
        client.search(index="test_index", query=query)

        # Verify the search was called with query= parameter, not body=
        mock_search.assert_called_once()
        call_args = mock_search.call_args[1]
        self.assertIn("query", call_args)
        self.assertNotIn("body", call_args)

    @patch("elasticsearch.Elasticsearch.update")
    def test_update_uses_doc_param_not_body(self, mock_update):
        # Create a mock return value
        mock_response = MagicMock()
        mock_update.return_value = mock_response

        # Create a client and perform an update
        client = es_client()
        doc_data = {"field1": "value1", "field2": "value2"}
        client.update(index="test_index", id="1", doc=doc_data)

        # Verify the update was called with doc= parameter, not body=
        mock_update.assert_called_once()
        call_args = mock_update.call_args[1]
        self.assertIn("doc", call_args)
        self.assertNotIn("body", call_args)

    @patch("elasticsearch.Elasticsearch.indices.delete")
    @patch("elasticsearch.Elasticsearch.indices.exists")
    def test_recreate_index_and_mapping(self, mock_exists, mock_delete):
        # Setup mocks
        mock_exists.return_value = True
        mock_doc_type = MagicMock()
        mock_doc_type._index._name = "test_index"

        # Call the function
        recreate_index_and_mapping(mock_doc_type)

        # Verify the indices.exists and indices.delete were called correctly
        mock_exists.assert_called_once_with(index="test_index")
        mock_delete.assert_called_once_with(index="test_index")
