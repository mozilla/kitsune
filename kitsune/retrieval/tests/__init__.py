from dataclasses import dataclass
from datetime import UTC, datetime

from elasticsearch.helpers import scan

from kitsune.retrieval.index import (
    CHUNK_KIND,
    ChunkDocument,
    ChunkIdentity,
    ExpectedDocumentState,
    configured_index_meta,
    create_write_generation,
    read_manifest,
)
from kitsune.search.es_utils import es_client
from kitsune.search.tests import ElasticTestCase


@dataclass(frozen=True)
class IndexedDocumentState:
    """Full stored state used only by tests that inspect Elasticsearch writes."""

    manifest: ExpectedDocumentState | None
    chunks: list[dict]


def read_indexed_document(*, index: str, identity: ChunkIdentity) -> IndexedDocumentState:
    filters = [
        {"term": {"content_type": identity.content_type}},
        {"term": {"object_id": identity.object_id}},
        {"term": {"locale": identity.locale}},
        {"term": {"kind": CHUNK_KIND}},
    ]
    hits = scan(
        es_client(),
        index=index,
        query={
            "query": {"bool": {"filter": filters}},
            "_source": {"exclude_vectors": False},
        },
    )
    chunks = sorted((hit["_source"] for hit in hits), key=lambda item: item["position"])
    return IndexedDocumentState(
        manifest=read_manifest(index=index, identity=identity),
        chunks=chunks,
    )


class ChunkIndexTestCase(ElasticTestCase):
    """Create/drop the chunk index per test class — it isn't in `get_doc_types()`, so the
    shared `es_init` doesn't build it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # a crashed run can leave an alias-less orphan index; start from a clean slate
        cls._delete_indices()
        create_write_generation(timestamp=datetime.now(tz=UTC), meta=configured_index_meta())
        ChunkDocument.migrate_reads()

    @classmethod
    def tearDownClass(cls):
        cls._delete_indices()
        super().tearDownClass()

    @classmethod
    def _delete_indices(cls):
        es_client().indices.delete(
            index=f"{ChunkDocument.Index.base_name}_*", ignore_unavailable=True
        )

    def tearDown(self):
        # conflicts="proceed" so cleanup ignores version conflicts from concurrent refreshes
        es_client().delete_by_query(
            index=ChunkDocument.Index.write_alias,
            query={"match_all": {}},
            conflicts="proceed",
            refresh=True,
        )
        super().tearDown()
