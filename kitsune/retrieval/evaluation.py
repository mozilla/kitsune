"""Frozen, environment-specific relevance evaluation for the retrieval read path.

The positive set is derived from solved questions whose accepted answer cites a KB article.
It is a relevance proxy rather than complete ground truth: a labelled KB family is relevant,
but an unlabelled result is not necessarily irrelevant. A separate manually reviewed artifact
represents queries for which the current corpus has no useful answer.
"""

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import datetime
from math import log2
from typing import Literal
from urllib.parse import urlparse

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from lxml import html as lxml_html

from kitsune.products.models import Product
from kitsune.questions.models import Question
from kitsune.retrieval.access import (
    AuthorizedCandidate,
    AuthorizedPassage,
    ViewerAccess,
    authorize_candidates,
)
from kitsune.retrieval.eligibility import eligible_documents
from kitsune.retrieval.embeddings import EmbeddingRecipe, get_embeddings, recipe_to_payload
from kitsune.retrieval.fingerprints import canonical_json
from kitsune.retrieval.query import (
    AAQ_SOURCE,
    ENGLISH_LOCALE,
    KB_SOURCE,
    RRF_RANK_CONSTANT,
    DefaultOperator,
    LocaleComposition,
    RetrievalResult,
    _retrieve_unvalidated,
)
from kitsune.search.search import WikiSearch
from kitsune.sumo.parser import wiki_to_html
from kitsune.wiki.models import Document, get_locale_and_slug_from_document_url

ArtifactKind = Literal["positive", "no_answer"]
EvaluationSplit = Literal["tuning", "holdout"]

ARTIFACT_SCHEMA_VERSION = 1
DERIVATION = "solved-question-cites-kb-family/3"
NO_ANSWER_DERIVATION = "manually-reviewed-no-answer/1"
DEFAULT_K_VALUES = (1, 3, 10)
_NDCG_CUTOFF = 10
_HOLDOUT_MODULUS = 5
_EMBEDDING_BATCH_SIZE = 100
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ROOT_RELATIVE_KB_LINK = re.compile(r"(?<![A-Za-z0-9:/])(/kb/[A-Za-z0-9_-]+)")


class InvalidEvaluationArtifact(ValueError):
    """An evaluation artifact is malformed, changed, or belongs to another contract."""


class InvalidEvaluationResult(ValueError):
    """An evaluated search backend returned a result that cannot be scored."""


@dataclass(frozen=True)
class EvaluationQuery:
    query_id: str
    query: str
    locale: str
    relevant_family_ids: tuple[str, ...]
    source_family_id: str | None
    product_id: int | None
    split: EvaluationSplit


@dataclass(frozen=True)
class EvaluationArtifact:
    kind: ArtifactKind
    environment: str
    created_at: str
    read_generation: str
    derivation: str
    queries: tuple[EvaluationQuery, ...]
    digest: str
    schema_version: int = ARTIFACT_SCHEMA_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: object) -> EvaluationArtifact:
        if not isinstance(payload, Mapping):
            raise InvalidEvaluationArtifact("artifact must be a JSON object")
        if set(payload) != {item.name for item in fields(cls)}:
            raise InvalidEvaluationArtifact("artifact fields do not match the schema")
        try:
            values = dict(payload)
            values["queries"] = tuple(_query_from_payload(item) for item in payload["queries"])
            artifact = cls(**values)
            _validate_artifact(artifact)
        except InvalidEvaluationArtifact:
            raise
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise InvalidEvaluationArtifact(f"artifact has invalid fields: {exc}") from exc
        return artifact


@dataclass(frozen=True)
class RelevanceScore:
    queries: int
    recall_at_k: dict[int, float] = field(default_factory=dict)
    ndcg_at_10: float = 0.0
    empty_results: int = 0
    missed_query_ids: tuple[str, ...] = ()

    def to_payload(self) -> dict:
        payload = asdict(self)
        payload["recall_at_k"] = {str(k): value for k, value in self.recall_at_k.items()}
        return payload


@dataclass(frozen=True)
class EvaluationConfig:
    similarity_floor: float
    similarity_profile: str
    semantic_k: int
    num_candidates: int
    rank_window_size: int
    default_operator: DefaultOperator
    minimum_should_match: str | None
    locale_composition: LocaleComposition

    def __post_init__(self):
        if (
            isinstance(self.similarity_floor, bool)
            or not isinstance(self.similarity_floor, int | float)
            or not -1 <= self.similarity_floor <= 1
        ):
            raise ValueError("similarity_floor must be between -1 and 1")
        if not _SHA256.fullmatch(self.similarity_profile):
            raise ValueError("similarity_profile must be a SHA-256 digest")
        for name in ("semantic_k", "num_candidates", "rank_window_size"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.num_candidates < self.semantic_k:
            raise ValueError("num_candidates must be at least semantic_k")
        if self.rank_window_size < _NDCG_CUTOFF + 1:
            raise ValueError("rank_window_size must fit the evaluation depth and next-hit probe")
        if self.default_operator not in ("AND", "OR"):
            raise ValueError("default_operator must be AND or OR")
        if self.locale_composition not in ("combined", "separate"):
            raise ValueError("locale_composition must be combined or separate")
        if self.default_operator == "AND" and self.minimum_should_match is not None:
            raise ValueError("minimum_should_match applies only to OR")
        if self.default_operator == "OR" and not self.minimum_should_match:
            raise ValueError("OR requires minimum_should_match")

    def to_payload(self) -> dict:
        return {**asdict(self), "rank_constant": RRF_RANK_CONSTANT}


def build_positive_artifact(
    *,
    environment: str,
    read_generation: str,
    locales: Sequence[str] = (),
    limit: int | None = None,
) -> EvaluationArtifact:
    """Derive labelled queries from accepted answers that cite eligible KB families."""
    questions = (
        Question.objects.filter(solution__isnull=False, is_spam=False, solution__is_spam=False)
        .filter(Q(solution__content__icontains="/kb/") | Q(solution__content__contains="[["))
        .select_related("solution")
        .only("id", "title", "locale", "product_id", "solution__content")
        .order_by("pk")
    )
    if locales := tuple(locales):
        questions = questions.filter(locale__in=locales)

    documents = list(
        eligible_documents()
        .select_related(None)
        .prefetch_related(None)
        .values_list("slug", "locale", "id", "parent_id")
    )
    family_ids = {parent_id or document_id for _, _, document_id, parent_id in documents}
    family_products: dict[int, set[int]] = {family_id: set() for family_id in family_ids}
    for document_id, product_id in Document.products.through.objects.filter(
        document_id__in=family_ids
    ).values_list("document_id", "product_id"):
        family_products[document_id].add(product_id)

    eligible = {
        (locale, slug): (
            parent_id or document_id,
            family_products[parent_id or document_id],
        )
        for slug, locale, document_id, parent_id in documents
    }
    eligible_families = {
        (parent_id or document_id, locale) for _, locale, document_id, parent_id in documents
    }

    records = []
    seen = set()
    for question in questions.iterator(chunk_size=1000):
        query = (question.title or "").strip()
        if not query or len(query) > 200:
            continue
        relevant = set()
        for url in _kb_links(question.solution.content or "", question.locale):
            key = _document_key(url, question.locale)
            if key is None or key not in eligible:
                continue
            family_id, product_ids = eligible[key]
            if (family_id, question.locale) not in eligible_families:
                continue
            if question.product_id and question.product_id not in product_ids:
                continue
            relevant.add(f"{KB_SOURCE}:{family_id}")
        if not relevant:
            continue

        relevant_family_ids = tuple(sorted(relevant))
        pair_key = (query, question.locale, question.product_id, relevant_family_ids)
        if pair_key in seen:
            continue
        seen.add(pair_key)
        query_id = f"{AAQ_SOURCE}:{question.id}"
        records.append(
            EvaluationQuery(
                query_id=query_id,
                query=query,
                locale=question.locale,
                relevant_family_ids=relevant_family_ids,
                source_family_id=query_id,
                product_id=question.product_id,
                split=_split_for(query_id),
            )
        )
        if limit and len(records) >= limit:
            break

    return _freeze_artifact(
        kind="positive",
        environment=environment,
        read_generation=read_generation,
        derivation=DERIVATION,
        queries=records,
    )


def freeze_no_answer_artifact(
    records: Sequence[Mapping], *, environment: str, read_generation: str
) -> EvaluationArtifact:
    """Freeze a manually reviewed list of current-corpus no-answer queries."""
    queries = []
    seen = set()
    for record in records:
        if not isinstance(record, Mapping) or set(record) - {"query", "locale", "product_id"}:
            raise InvalidEvaluationArtifact(
                "no-answer records accept only query, locale, and optional product_id"
            )
        query = record.get("query")
        locale = record.get("locale")
        product_id = record.get("product_id")
        if not isinstance(query, str) or not query.strip():
            raise InvalidEvaluationArtifact("no-answer query must be a non-empty string")
        if not isinstance(locale, str) or not locale:
            raise InvalidEvaluationArtifact("no-answer locale must be a non-empty string")
        if product_id is not None and (
            not isinstance(product_id, int) or isinstance(product_id, bool) or product_id <= 0
        ):
            raise InvalidEvaluationArtifact("no-answer product_id must be a positive integer")
        query = query.strip()
        query_id = (
            f"no-answer:{hashlib.sha256(canonical_json([query, locale, product_id])).hexdigest()}"
        )
        if query_id in seen:
            raise InvalidEvaluationArtifact("no-answer records must be unique")
        seen.add(query_id)
        queries.append(
            EvaluationQuery(
                query_id=query_id,
                query=query,
                locale=locale,
                relevant_family_ids=(),
                source_family_id=None,
                product_id=product_id,
                split=_split_for(query_id),
            )
        )
    return _freeze_artifact(
        kind="no_answer",
        environment=environment,
        read_generation=read_generation,
        derivation=NO_ANSWER_DERIVATION,
        queries=queries,
    )


def score_rankings(
    queries: Sequence[EvaluationQuery],
    rankings: Mapping[str, Sequence[str]],
    *,
    k_values: Sequence[int] = DEFAULT_K_VALUES,
) -> RelevanceScore:
    """Score family rankings against positive labels without assuming labels are exhaustive."""
    k_values = tuple(sorted(set(k_values)))
    expected_ids = {query.query_id for query in queries}
    if set(rankings) != expected_ids:
        raise ValueError("rankings must contain exactly one result for every evaluation query")

    found = dict.fromkeys(k_values, 0.0)
    ndcg_total = 0.0
    misses = []
    for query in queries:
        ranked = list(dict.fromkeys(rankings[query.query_id]))
        relevant = set(query.relevant_family_ids)
        if not relevant:
            raise ValueError("relevance scoring requires at least one label per query")
        for k in k_values:
            found[k] += len(relevant.intersection(ranked[:k])) / len(relevant)
        ndcg_total += _ndcg(ranked[:_NDCG_CUTOFF], relevant)
        if not relevant.intersection(ranked[:_NDCG_CUTOFF]):
            misses.append(query.query_id)

    count = len(queries)
    return RelevanceScore(
        queries=count,
        recall_at_k={k: (found[k] / count if count else 0.0) for k in k_values},
        ndcg_at_10=(ndcg_total / count if count else 0.0),
        empty_results=sum(not rankings[query.query_id] for query in queries),
        missed_query_ids=tuple(misses),
    )


def score_no_answer(
    queries: Sequence[EvaluationQuery],
    semantic_rankings: Mapping[str, Sequence[str]],
    hybrid_rankings: Mapping[str, Sequence[str]],
) -> dict:
    """Keep semantic and full-hybrid returns separate for manual false-positive review."""
    expected_ids = {query.query_id for query in queries}
    if set(semantic_rankings) != expected_ids or set(hybrid_rankings) != expected_ids:
        raise ValueError("no-answer rankings must cover the complete selected artifact")

    def returned(rankings):
        return {query_id: list(families) for query_id, families in rankings.items() if families}

    semantic_returns = returned(semantic_rankings)
    hybrid_returns = returned(hybrid_rankings)
    return {
        "queries": len(queries),
        "semantic_kb_returns": len(semantic_returns),
        "full_hybrid_returns": len(hybrid_returns),
        "semantic_returned_query_ids": sorted(semantic_returns),
        "hybrid_returned_query_ids": sorted(hybrid_returns),
        "semantic_families_for_review": semantic_returns,
        "hybrid_families_for_review": hybrid_returns,
    }


def evaluate_artifacts(
    positive: EvaluationArtifact,
    no_answer: EvaluationArtifact,
    *,
    environment: str,
    read_generation: str,
    recipe: EmbeddingRecipe,
    config: EvaluationConfig,
    split: EvaluationSplit,
) -> dict:
    """Evaluate one explicit configuration against frozen positive and no-answer sets."""
    _validate_evaluation_inputs(positive, no_answer, environment, read_generation)
    positives = tuple(query for query in positive.queries if query.split == split)
    no_answers = tuple(query for query in no_answer.queries if query.split == split)
    if not positives or not no_answers:
        raise ValueError(f"the {split} split must contain positive and no-answer queries")
    product_ids = {query.product_id for query in (*positives, *no_answers) if query.product_id}
    products = Product.objects.in_bulk(product_ids)
    if set(products) != product_ids:
        raise ValueError("an evaluation artifact references a product that no longer exists")

    rankings: dict[str, dict[str, list[str]]] = {
        mode: {} for mode in ("current_lexical", "new_lexical", "semantic_only", "rrf")
    }
    no_answer_semantic: dict[str, list[str]] = {}
    no_answer_hybrid: dict[str, list[str]] = {}
    mixed_rankings: dict[str, list[str]] = {}
    semantic_distributions: dict[str, tuple[tuple[str, int], ...]] = {}
    evidence_locales: Counter[str] = Counter()

    selected = [*positives, *no_answers]
    positive_ids = {query.query_id for query in positives}
    for start in range(0, len(selected), _EMBEDDING_BATCH_SIZE):
        batch = selected[start : start + _EMBEDDING_BATCH_SIZE]
        vectors = get_embeddings([query.query for query in batch], task="query", recipe=recipe)
        for query, vector in zip(batch, vectors, strict=True):
            if query.query_id in positive_ids:
                rankings["current_lexical"][query.query_id] = _current_lexical_ranking(
                    query, products.get(query.product_id)
                )
                rankings["new_lexical"][query.query_id] = _families(
                    _run_retrieval(
                        query,
                        vector=None,
                        config=config,
                        read_generation=read_generation,
                        sources={KB_SOURCE},
                    )
                )
                semantic = _run_retrieval(
                    query,
                    vector=vector,
                    config=config,
                    read_generation=read_generation,
                    sources={KB_SOURCE},
                    include_lexical=False,
                    family_distribution_size=config.semantic_k,
                )
                rankings["semantic_only"][query.query_id] = _families(semantic)
                semantic_distributions[query.query_id] = semantic.family_counts

                kb_rrf = _run_retrieval(
                    query,
                    vector=vector,
                    config=config,
                    read_generation=read_generation,
                    sources={KB_SOURCE},
                )
                rankings["rrf"][query.query_id] = _families(kb_rrf)
                if query.locale != ENGLISH_LOCALE:
                    evidence_locales.update(_evidence_locales(kb_rrf, query.locale))
                mixed = _run_retrieval(
                    query,
                    vector=vector,
                    config=config,
                    read_generation=read_generation,
                    sources={KB_SOURCE, AAQ_SOURCE},
                    excluded_family_ids=(query.source_family_id,)
                    if query.source_family_id
                    else (),
                )
                mixed_families = _families(mixed)
                if query.source_family_id in mixed_families:
                    raise ValueError("mixed evaluation returned its source AAQ family")
                mixed_rankings[query.query_id] = mixed_families
            else:
                semantic = _run_retrieval(
                    query,
                    vector=vector,
                    config=config,
                    read_generation=read_generation,
                    sources={KB_SOURCE},
                    include_lexical=False,
                )
                no_answer_semantic[query.query_id] = _families(semantic)
                hybrid = _run_retrieval(
                    query,
                    vector=vector,
                    config=config,
                    read_generation=read_generation,
                    sources={KB_SOURCE, AAQ_SOURCE},
                )
                no_answer_hybrid[query.query_id] = _families(hybrid)

    report = {
        "schema_version": 1,
        "created_at": timezone.now().isoformat(),
        "environment": environment,
        "read_generation": read_generation,
        "positive_artifact_digest": positive.digest,
        "no_answer_artifact_digest": no_answer.digest,
        "split": split,
        "recipe": recipe_to_payload(recipe),
        "configuration": config.to_payload(),
        "positive": {
            mode: score_rankings(positives, mode_rankings).to_payload()
            for mode, mode_rankings in rankings.items()
        },
        "no_answer": score_no_answer(no_answers, no_answer_semantic, no_answer_hybrid),
        "mixed": _mixed_diagnostics(positives, rankings["rrf"], mixed_rankings),
        "semantic_candidate_diversity": _semantic_diversity(semantic_distributions),
        "evidence_locale_counts": dict(evidence_locales),
    }
    return report


def _run_retrieval(
    query: EvaluationQuery,
    *,
    vector: Sequence[float] | None,
    config: EvaluationConfig,
    read_generation: str,
    sources: set[Literal["kb", "aaq"]],
    include_lexical: bool = True,
    excluded_family_ids: Sequence[str] = (),
    family_distribution_size: int | None = None,
) -> RetrievalResult[AuthorizedCandidate]:
    unvalidated = _retrieve_unvalidated(
        query.query,
        kb_index=read_generation,
        locale=query.locale,
        sources=sources,
        viewer_group_ids=(),
        product_id=query.product_id,
        query_vector=vector,
        similarity_floor=config.similarity_floor if vector is not None else None,
        semantic_k=config.semantic_k,
        num_candidates=config.num_candidates,
        rank_window_size=config.rank_window_size,
        locale_composition=config.locale_composition,
        page_size=_NDCG_CUTOFF,
        default_operator=config.default_operator,
        minimum_should_match=config.minimum_should_match,
        strict=True,
        include_lexical=include_lexical,
        excluded_family_ids=excluded_family_ids,
        family_distribution_size=family_distribution_size,
    )
    return authorize_candidates(
        unvalidated,
        viewer_access=ViewerAccess(),
        locale=query.locale,
        product_id=query.product_id,
        page_size=_NDCG_CUTOFF,
    )


def _current_lexical_ranking(query: EvaluationQuery, product: Product | None) -> list[str]:
    search = WikiSearch(query=query.query, locale=query.locale, product=product)
    try:
        search.run(slice(0, _NDCG_CUTOFF))
    except KeyError as exc:
        raise InvalidEvaluationResult(
            "the legacy Wiki index returned a malformed result; repair or reindex "
            "WikiDocument before evaluation"
        ) from exc

    families = []
    for result in search.results:
        try:
            families.append(f"{KB_SOURCE}:{int(result['id'])}")
        except KeyError, TypeError, ValueError:
            continue
    return families


def _families(result: RetrievalResult[AuthorizedCandidate]) -> list[str]:
    return [candidate.family_id for candidate in result.candidates]


def _evidence_locales(
    result: RetrievalResult[AuthorizedCandidate], requested_locale: str
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for candidate in result.candidates:
        if isinstance(candidate.evidence, AuthorizedPassage):
            key = "requested" if candidate.evidence.passage.locale == requested_locale else "en-US"
            counts[key] += 1
    return counts


def _mixed_diagnostics(
    queries: Sequence[EvaluationQuery],
    kb_rankings: Mapping[str, Sequence[str]],
    mixed_rankings: Mapping[str, Sequence[str]],
) -> dict:
    source_counts: Counter[str] = Counter()
    displaced = []
    for query in queries:
        mixed = list(mixed_rankings[query.query_id])
        source_counts.update(family.split(":", 1)[0] for family in mixed)
        relevant = set(query.relevant_family_ids)
        kb_rank = _best_rank(kb_rankings[query.query_id], relevant)
        mixed_rank = _best_rank(mixed, relevant)
        if kb_rank is not None and (mixed_rank is None or mixed_rank > kb_rank):
            displaced.append(query.query_id)
    return {
        "queries": len(queries),
        "result_source_counts": dict(source_counts),
        "kb_label_displaced_queries": len(displaced),
        "kb_label_displaced_query_ids": displaced,
        "unlabelled_aaq_treated_as_irrelevant": False,
    }


def _semantic_diversity(distributions: Mapping[str, Sequence[tuple[str, int]]]) -> dict:
    unique_counts = []
    largest_shares = []
    for counts in distributions.values():
        total = sum(count for _, count in counts)
        unique_counts.append(len(counts))
        largest_shares.append(
            max((count for _, count in counts), default=0) / total if total else 0
        )
    query_count = len(distributions)
    return {
        "queries": query_count,
        "average_unique_families": sum(unique_counts) / query_count if query_count else 0.0,
        "largest_per_family_chunk_share": max(largest_shares, default=0.0),
    }


def _best_rank(ranking: Sequence[str], relevant: set[str]) -> int | None:
    return next((rank for rank, family in enumerate(ranking, start=1) if family in relevant), None)


def _ndcg(ranked: Sequence[str], relevant: set[str]) -> float:
    if not relevant:
        return 0.0
    gain = sum(
        1 / log2(position + 2) for position, family in enumerate(ranked) if family in relevant
    )
    ideal = sum(1 / log2(position + 2) for position in range(min(len(relevant), _NDCG_CUTOFF)))
    return gain / ideal


def _freeze_artifact(
    *,
    kind: ArtifactKind,
    environment: str,
    read_generation: str,
    derivation: str,
    queries: Sequence[EvaluationQuery],
) -> EvaluationArtifact:
    artifact = EvaluationArtifact(
        kind=kind,
        environment=environment,
        created_at=timezone.now().isoformat(),
        read_generation=read_generation,
        derivation=derivation,
        queries=tuple(queries),
        digest="",
    )
    digest = hashlib.sha256(canonical_json(_artifact_payload(artifact))).hexdigest()
    artifact = replace(artifact, digest=digest)
    _validate_artifact(artifact)
    return artifact


def _artifact_payload(artifact: EvaluationArtifact) -> dict:
    payload = asdict(artifact)
    payload.pop("digest")
    return payload


def _query_from_payload(payload: object) -> EvaluationQuery:
    if not isinstance(payload, Mapping):
        raise InvalidEvaluationArtifact("artifact query must be an object")
    if set(payload) != {item.name for item in fields(EvaluationQuery)}:
        raise InvalidEvaluationArtifact("artifact query fields do not match the schema")
    try:
        values = dict(payload)
        values["relevant_family_ids"] = tuple(payload["relevant_family_ids"])
        return EvaluationQuery(**values)
    except (KeyError, TypeError) as exc:
        raise InvalidEvaluationArtifact(f"artifact query has invalid fields: {exc}") from exc


def _validate_artifact(artifact: EvaluationArtifact) -> None:
    if artifact.schema_version != ARTIFACT_SCHEMA_VERSION:
        raise InvalidEvaluationArtifact("artifact schema version is unsupported")
    if artifact.kind not in ("positive", "no_answer"):
        raise InvalidEvaluationArtifact("artifact kind is invalid")
    if not isinstance(artifact.environment, str) or not artifact.environment:
        raise InvalidEvaluationArtifact("artifact environment is invalid")
    if not isinstance(artifact.read_generation, str) or not artifact.read_generation:
        raise InvalidEvaluationArtifact("artifact read generation is invalid")
    try:
        created_at = datetime.fromisoformat(artifact.created_at)
    except (TypeError, ValueError) as exc:
        raise InvalidEvaluationArtifact("artifact creation time is invalid") from exc
    if created_at.tzinfo is None or created_at.utcoffset() is None:
        raise InvalidEvaluationArtifact("artifact creation time must be timezone-aware")
    expected_derivation = DERIVATION if artifact.kind == "positive" else NO_ANSWER_DERIVATION
    if artifact.derivation != expected_derivation:
        raise InvalidEvaluationArtifact("artifact derivation is incompatible with this code")

    query_ids = set()
    for query in artifact.queries:
        if (
            not isinstance(query.query_id, str)
            or not query.query_id
            or query.query_id in query_ids
        ):
            raise InvalidEvaluationArtifact("artifact query IDs must be non-empty and unique")
        query_ids.add(query.query_id)
        if not isinstance(query.query, str) or not query.query or len(query.query) > 200:
            raise InvalidEvaluationArtifact("artifact query must contain 1 to 200 characters")
        if not isinstance(query.locale, str) or not query.locale:
            raise InvalidEvaluationArtifact("artifact query locale is invalid")
        if query.product_id is not None and (
            not isinstance(query.product_id, int)
            or isinstance(query.product_id, bool)
            or query.product_id <= 0
        ):
            raise InvalidEvaluationArtifact("artifact query product is invalid")
        if query.split != _split_for(query.query_id):
            raise InvalidEvaluationArtifact("artifact query split is not deterministic")
        if artifact.kind == "positive":
            if (
                not query.relevant_family_ids
                or query.relevant_family_ids != tuple(sorted(set(query.relevant_family_ids)))
                or any(
                    not isinstance(family, str) or not family.startswith(f"{KB_SOURCE}:")
                    for family in query.relevant_family_ids
                )
                or query.source_family_id != query.query_id
                or not query.query_id.startswith(f"{AAQ_SOURCE}:")
            ):
                raise InvalidEvaluationArtifact("positive query identities are invalid")
        elif query.relevant_family_ids or query.source_family_id is not None:
            raise InvalidEvaluationArtifact("no-answer queries cannot carry relevance labels")

    if not isinstance(artifact.digest, str) or not _SHA256.fullmatch(artifact.digest):
        raise InvalidEvaluationArtifact("artifact digest is invalid")
    expected_digest = hashlib.sha256(canonical_json(_artifact_payload(artifact))).hexdigest()
    if artifact.digest != expected_digest:
        raise InvalidEvaluationArtifact("artifact digest does not match its contents")


def _validate_evaluation_inputs(
    positive: EvaluationArtifact,
    no_answer: EvaluationArtifact,
    environment: str,
    read_generation: str,
) -> None:
    _validate_artifact(positive)
    _validate_artifact(no_answer)
    if positive.kind != "positive" or no_answer.kind != "no_answer":
        raise InvalidEvaluationArtifact("evaluation requires positive and no-answer artifacts")
    if {positive.environment, no_answer.environment} != {environment}:
        raise InvalidEvaluationArtifact("artifacts belong to a different environment")
    if {positive.read_generation, no_answer.read_generation} != {read_generation}:
        raise InvalidEvaluationArtifact("artifacts belong to a different read generation")


def validate_split_coverage(artifact: EvaluationArtifact) -> None:
    """Reject an artifact that cannot support both documented evaluation passes."""
    splits = {query.split for query in artifact.queries}
    if splits != {"tuning", "holdout"}:
        raise InvalidEvaluationArtifact(
            "artifact must contain at least one tuning and one holdout query"
        )


def _split_for(query_id: str) -> EvaluationSplit:
    digest = hashlib.sha256(query_id.encode()).digest()
    return "holdout" if int.from_bytes(digest[:8], "big") % _HOLDOUT_MODULUS == 0 else "tuning"


def _kb_links(markup: str, locale: str) -> set[str]:
    rendered = wiki_to_html(markup, locale=locale)
    root = lxml_html.fragment_fromstring(rendered, create_parent="div")
    links = set(root.xpath(".//a[@href]/@href"))
    links.update(_ROOT_RELATIVE_KB_LINK.findall(markup))
    return links


def _document_key(url: str, default_locale: str) -> tuple[str, str] | None:
    parsed = urlparse(url)
    canonical_host = urlparse(settings.CANONICAL_URL).netloc.casefold()
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc and parsed.netloc.casefold() != canonical_host:
        return None
    if parsed.path.startswith("/kb/"):
        parsed = parsed._replace(path=f"/{default_locale}{parsed.path}")
    return get_locale_and_slug_from_document_url(parsed.geturl())
