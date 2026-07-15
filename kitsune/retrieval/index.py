from dataclasses import dataclass
from datetime import UTC, datetime

from django.conf import settings
from elasticsearch.dsl import field
from elasticsearch.dsl.types import DenseVectorIndexOptions
from elasticsearch.helpers import bulk

from kitsune.retrieval.chunking import Chunk
from kitsune.search.base import SumoDocument
from kitsune.search.es_utils import es_client
from kitsune.search.fields import SumoLocaleAwareKeywordField, SumoLocaleAwareTextField

# Must match the embedding model's output dimensionality.
VECTOR_DIMS = 768


class ChunkDocument(SumoDocument):
    content_text = SumoLocaleAwareTextField()
    content_vector = field.DenseVector(
        dims=VECTOR_DIMS,
        similarity="cosine",
        index=True,
        index_options=DenseVectorIndexOptions(type="hnsw", m=16, ef_construction=100),
    )

    content_type = field.Keyword()
    object_id = field.Keyword()
    family_id = field.Keyword()
    locale = field.Keyword()
    applies_to = field.Keyword(multi=True)
    heading_path = field.Text()
    position = field.Integer()
    content_hash = field.Keyword()

    # source-document metadata, denormalized onto every chunk
    title = SumoLocaleAwareTextField()
    summary = SumoLocaleAwareTextField()
    keywords = SumoLocaleAwareTextField()
    slug = SumoLocaleAwareKeywordField()
    category = field.Keyword()
    product_ids = field.Keyword(multi=True)
    topic_ids = field.Keyword(multi=True)
    updated = field.Date()

    class Index:
        pass


@dataclass(frozen=True)
class ChunkSource:
    """Identity and denormalized metadata of the source record a set of chunks
    belongs to, shared across all of its chunks."""

    content_type: str
    object_id: str
    locale: str
    family_id: str
    title: str
    summary: str
    keywords: str
    slug: str
    category: str
    product_ids: list[str]
    topic_ids: list[str]
    updated: datetime
    content_hash: str


def index_chunks(chunks: list[Chunk], source: ChunkSource) -> None:
    locale = source.locale
    indexed_on = datetime.now(tz=UTC)
    actions = []
    for chunk in chunks:
        doc = ChunkDocument(
            content_text={locale: chunk.text},
            content_type=source.content_type,
            object_id=source.object_id,
            family_id=source.family_id,
            locale=locale,
            applies_to=sorted(chunk.applies_to),
            heading_path=chunk.heading_path,
            position=chunk.position,
            content_hash=source.content_hash,
            indexed_on=indexed_on,
            title={locale: source.title},
            summary={locale: source.summary},
            keywords={locale: source.keywords},
            slug={locale: source.slug},
            category=source.category,
            product_ids=source.product_ids,
            topic_ids=source.topic_ids,
            updated=source.updated,
        )
        doc.meta.id = f"{source.content_type}:{source.object_id}:{locale}:{chunk.position}"
        actions.append(doc.to_action(action="index", is_bulk=True))

    bulk(
        es_client(),
        actions,
        chunk_size=settings.ES_DEFAULT_ELASTIC_CHUNK_SIZE,
        refresh=settings.TEST,
    )
