from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from django.test.utils import override_settings
from elastic_transport import ApiResponseMeta, ConnectionTimeout, HttpHeaders
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.dsl import connections
from elasticsearch.helpers.errors import BulkIndexError

from kitsune.questions.models import Question
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.search.base import SumoDocument
from kitsune.search.config import DEFAULT_ES_CONNECTION
from kitsune.search.documents import QuestionDocument
from kitsune.search.es_utils import index_objects_bulk
from kitsune.search.tests import ElasticTestCase, _initialize_indices


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


class IndexInitializationTests(SimpleTestCase):
    def test_timed_out_creation_preserves_the_query_client(self):
        original = connections.get_connection(DEFAULT_ES_CONNECTION)
        client = Elasticsearch(
            "http://localhost:9200", request_timeout=1, retry_on_timeout=True, max_retries=1
        )
        self.addCleanup(client.close)
        self.addCleanup(connections.add_connection, DEFAULT_ES_CONNECTION, original)
        connections.add_connection(DEFAULT_ES_CONNECTION, client)
        node = client.transport.node_pool.get()
        created = False

        def response(status, body=b""):
            return SimpleNamespace(
                meta=ApiResponseMeta(
                    status=status,
                    http_version="1.1",
                    headers=HttpHeaders(
                        {"content-type": "application/json", "x-elastic-product": "Elasticsearch"}
                    ),
                    duration=0,
                    node=node.config,
                ),
                body=body,
            )

        def perform_request(method, target, *, request_timeout, **kwargs):
            nonlocal created
            if method == "HEAD":
                return response(200 if created else 404)
            if method == "PUT":
                if created:
                    return response(
                        400, b'{"error":{"type":"resource_already_exists_exception"},"status":400}'
                    )
                created = True
                raise ConnectionTimeout("Index created, but its response was lost")
            if method == "GET" and target == "/":
                if request_timeout < 2:
                    raise ConnectionTimeout("Query exceeded its original one-second budget")
                return response(200, b"{}")
            self.fail(f"Unexpected Elasticsearch request: {method} {target}")

        with patch.object(node, "perform_request", side_effect=perform_request):
            # A replay would replace the original timeout with an "already exists" error.
            with self.assertRaises(ConnectionTimeout):
                # Exercise setup without discarding a worker's successful bootstrap.
                _initialize_indices.__wrapped__()
            # Failed setup must not leave subsequent requests using its longer timeout.
            with self.assertRaises(ConnectionTimeout):
                connections.get_connection(DEFAULT_ES_CONNECTION).options(max_retries=0).info()
