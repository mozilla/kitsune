from kitsune.retrieval.index import ChunkDocument
from kitsune.search.es_utils import es_client
from kitsune.search.tests import ElasticTestCase


class ChunkIndexTestCase(ElasticTestCase):
    """Create/drop the chunk index per test class — it isn't in `get_doc_types()`, so the
    shared `es_init` doesn't build it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # a crashed run can leave an alias-less orphan index; start from a clean slate
        cls._delete_indices()
        ChunkDocument.migrate_writes()
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
