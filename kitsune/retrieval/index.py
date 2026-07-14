from elasticsearch.dsl import field
from elasticsearch.dsl.types import DenseVectorIndexOptions

from kitsune.search.base import SumoDocument
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
