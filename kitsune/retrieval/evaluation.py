"""A relevance baseline for the search SuMo has today, so a later one can be compared to it.

The golden set is derived, not annotated. A question whose accepted solution links to a KB
article gives a labelled pair for free: the query is a real user's own phrasing, and the
relevant document is the article a support contributor chose after reading their problem.

Two properties of that derivation shape how the numbers must be read:

* **It is enriched for search failures.** Many people file a question after search did not help
  them, so absolute recall on this set is likely pessimistic. The comparable figure is the delta
  between two retrieval systems on identical pairs, not the absolute value.
* **Recall is a lower bound.** Only the cited article is labelled relevant, so a result that
  is a different-but-reasonable article scores as a miss.

Scores from differently derived sets are not comparable, so every set records the rule that
produced it (``DERIVATION``) alongside its generation stamp.
"""

import json
import re
from dataclasses import dataclass, field
from math import log2
from urllib.parse import urlparse

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from lxml import html as lxml_html

from kitsune.products.models import Product
from kitsune.questions.models import Question
from kitsune.retrieval.eligibility import eligible_documents
from kitsune.search.search import WikiSearch
from kitsune.sumo.parser import wiki_to_html
from kitsune.wiki.models import Document, get_locale_and_slug_from_document_url

# Bump when the derivation rule changes: it invalidates comparison with older sets.
DERIVATION = "solved-question-cites-kb-article/2"

DEFAULT_K_VALUES = (1, 3, 5, 10)
_NDCG_CUTOFF = 10
# The wiki parser turns full URLs and [[internal links]] into anchors. Root-relative shorthand
# is not linkified, so retain it explicitly without also matching an external host's path.
_ROOT_RELATIVE_KB_LINK = re.compile(r"(?<![A-Za-z0-9:/])(/kb/[A-Za-z0-9_-]+)")


@dataclass(frozen=True)
class GoldenPair:
    """One real query and the documents a contributor treated as its answer."""

    query: str
    locale: str
    relevant_document_ids: tuple[int, ...]
    # Provenance, so a surprising pair can be traced back to the question it came from.
    question_id: int
    product_id: int | None = None


@dataclass(frozen=True)
class GoldenSet:
    generation: str
    derivation: str
    pairs: tuple[GoldenPair, ...] = ()

    def to_json(self) -> str:
        return json.dumps(
            {
                "generation": self.generation,
                "derivation": self.derivation,
                "pairs": [
                    {
                        "query": pair.query,
                        "locale": pair.locale,
                        # Sorted so re-deriving an unchanged corpus is byte-identical.
                        "relevant_document_ids": sorted(pair.relevant_document_ids),
                        "question_id": pair.question_id,
                        "product_id": pair.product_id,
                    }
                    for pair in self.pairs
                ],
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=False,
        )

    @classmethod
    def from_json(cls, payload) -> GoldenSet:
        return cls(
            generation=payload["generation"],
            derivation=payload["derivation"],
            pairs=tuple(
                GoldenPair(
                    query=item["query"],
                    locale=item["locale"],
                    relevant_document_ids=tuple(item["relevant_document_ids"]),
                    question_id=item["question_id"],
                    product_id=item.get("product_id"),
                )
                for item in payload["pairs"]
            ),
        )


@dataclass(frozen=True)
class RelevanceScore:
    """How a retrieval system performed against one golden set."""

    generation: str
    derivation: str
    queries: int = 0
    recall_at_k: dict[int, float] = field(default_factory=dict)
    ndcg_at_10: float = 0.0
    # Queries the system returned nothing at all for, which is a different failure from
    # returning the wrong thing.
    empty_results: int = 0


def build_golden_set(*, locales=(), limit: int | None = None, generation: str = "") -> GoldenSet:
    """Derive labelled pairs from questions whose accepted solution cites a KB article."""
    questions = (
        Question.objects.filter(solution__isnull=False, is_spam=False, solution__is_spam=False)
        .filter(Q(solution__content__icontains="/kb/") | Q(solution__content__contains="[["))
        .select_related("solution")
        .only("id", "title", "locale", "product_id", "solution__content")
        .order_by("pk")
    )
    if locales := tuple(locales):
        questions = questions.filter(locale__in=locales)

    # One lookup for the whole corpus. Labels use the family/original id because lexical search
    # stores every translation under that id; every later runner must return the same identity.
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

    pairs = []
    seen = set()
    for question in questions.iterator(chunk_size=1000):
        query = (question.title or "").strip()
        if not query:
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
            relevant.add(family_id)
        if not relevant:
            continue
        relevant_ids = tuple(sorted(relevant))
        pair_key = (query, question.locale, question.product_id, relevant_ids)
        if pair_key in seen:
            continue
        seen.add(pair_key)
        pairs.append(
            GoldenPair(
                query=query,
                locale=question.locale,
                relevant_document_ids=relevant_ids,
                question_id=question.id,
                product_id=question.product_id,
            )
        )
        if limit and len(pairs) >= limit:
            break

    return GoldenSet(
        generation=generation or _today(),
        derivation=DERIVATION,
        pairs=tuple(pairs),
    )


def _kb_links(markup: str, locale: str) -> set[str]:
    """Return KB-link candidates after rendering Kitsune's answer markup."""
    rendered = wiki_to_html(markup, locale=locale)
    root = lxml_html.fragment_fromstring(rendered, create_parent="div")
    links = set(root.xpath(".//a[@href]/@href"))
    links.update(_ROOT_RELATIVE_KB_LINK.findall(markup))
    return links


def _document_key(url: str, default_locale: str) -> tuple[str, str] | None:
    """Resolve a local KB URL to its explicit locale and slug."""
    parsed = urlparse(url)
    canonical_host = urlparse(settings.CANONICAL_URL).netloc.casefold()
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc and parsed.netloc.casefold() != canonical_host:
        return None
    if parsed.path.startswith("/kb/"):
        parsed = parsed._replace(path=f"/{default_locale}{parsed.path}")
    return get_locale_and_slug_from_document_url(parsed.geturl())


def _today() -> str:
    return timezone.now().date().isoformat()


def _ranked_document_ids(pair: GoldenPair, depth: int, product: Product | None) -> list[int]:
    """The document ids today's search returns, in rank order.

    Goes through the production ``WikiSearch`` rather than a reimplementation: a baseline that
    reimplements ranking measures the reimplementation.
    """
    search = WikiSearch(query=pair.query, locale=pair.locale, product=product)
    search.run(slice(0, depth))
    ids = []
    for result in search.results:
        try:
            ids.append(int(result["id"]))
        except KeyError, TypeError, ValueError:
            continue
    return ids


def score_lexical_search(golden: GoldenSet, *, k_values=DEFAULT_K_VALUES) -> RelevanceScore:
    """Score today's keyword search against a golden set.

    Recall@k is the headline because retrieval recall is the ceiling on any answer built from
    it; nDCG@10 is reported alongside because ordering is what the search UI exposes.
    """
    k_values = tuple(sorted(set(k_values)))
    depth = max((*k_values, _NDCG_CUTOFF))
    found = dict.fromkeys(k_values, 0.0)
    ndcg_total = 0.0
    empty = 0
    products = Product.objects.in_bulk(
        {pair.product_id for pair in golden.pairs if pair.product_id is not None}
    )

    for pair in golden.pairs:
        ranked = _ranked_document_ids(pair, depth, products.get(pair.product_id))
        if not ranked:
            empty += 1
        relevant = set(pair.relevant_document_ids)
        for k in k_values:
            hits = len(relevant.intersection(ranked[:k]))
            found[k] += hits / len(relevant) if relevant else 0.0
        ndcg_total += _ndcg(ranked[:_NDCG_CUTOFF], relevant)

    queries = len(golden.pairs)
    return RelevanceScore(
        generation=golden.generation,
        derivation=golden.derivation,
        queries=queries,
        recall_at_k={k: (found[k] / queries if queries else 0.0) for k in k_values},
        ndcg_at_10=(ndcg_total / queries) if queries else 0.0,
        empty_results=empty,
    )


def _ndcg(ranked: list[int], relevant: set[int]) -> float:
    """Binary-relevance nDCG: how close this ordering is to the best possible one."""
    if not relevant:
        return 0.0
    gain = sum(1 / log2(position + 2) for position, doc in enumerate(ranked) if doc in relevant)
    ideal = sum(1 / log2(position + 2) for position in range(min(len(relevant), _NDCG_CUTOFF)))
    return gain / ideal
