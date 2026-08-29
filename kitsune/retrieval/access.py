"""Authoritative viewer access and KB retrieval-result authorization."""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from time import perf_counter

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.db.models import Q

from kitsune.retrieval.eligibility import content_eligible_documents
from kitsune.retrieval.query import (
    ENGLISH_LOCALE,
    DefaultOperator,
    LegacyQuestion,
    LocaleComposition,
    RetrievalPassage,
    RetrievalResult,
    Source,
    UnvalidatedCandidate,
    _retrieve_unvalidated,
    parse_positive_integer_id,
)
from kitsune.retrieval.validation import is_positive_int
from kitsune.wiki.models import Document

PRIMARY_DATABASE = "default"


@dataclass(frozen=True)
class ViewerAccess:
    """The access facts resolved once from the current viewer."""

    group_ids: tuple[int, ...] = ()
    privileged: bool = False

    def __post_init__(self):
        if self.privileged and self.group_ids:
            raise ValueError("privileged access cannot carry group IDs")
        if self.group_ids != tuple(sorted(set(self.group_ids))) or any(
            not is_positive_int(group_id) for group_id in self.group_ids
        ):
            raise ValueError("group_ids must be sorted, unique positive integers")


@dataclass(frozen=True)
class DisplayDocument:
    document_id: int
    locale: str
    title: str
    slug: str
    summary: str


@dataclass(frozen=True)
class AuthorizedPassage:
    passage: RetrievalPassage
    display: DisplayDocument


@dataclass(frozen=True)
class AuthorizedCandidate:
    rank: int
    score: float
    family_id: str
    evidence: AuthorizedPassage | LegacyQuestion


def viewer_access_for(user: User | AnonymousUser) -> ViewerAccess:
    """Resolve group membership once; staff and superusers bypass restrictions."""
    if not user.is_authenticated:
        return ViewerAccess()
    if user.is_superuser:
        return ViewerAccess(privileged=True)

    memberships = tuple(user.groups.using(PRIMARY_DATABASE).values_list("id", "name"))
    if any(name == settings.STAFF_GROUP for _, name in memberships):
        return ViewerAccess(privileged=True)
    return ViewerAccess(tuple(sorted(group_id for group_id, _ in memberships)))


def retrieve(
    query: str,
    *,
    viewer_access: ViewerAccess,
    kb_index: str | None,
    locale: str,
    sources: Collection[Source],
    product_id: int | None,
    query_vector: Sequence[float] | None,
    similarity_floor: float | None,
    semantic_k: int,
    num_candidates: int,
    rank_window_size: int,
    locale_composition: LocaleComposition,
    page_size: int,
    default_operator: DefaultOperator = "AND",
    minimum_should_match: str | None = None,
    strict: bool = False,
    excluded_family_ids: Collection[str] = (),
) -> RetrievalResult[AuthorizedCandidate]:
    """Retrieve candidates and authorize every selected KB source against the primary DB."""
    if not is_positive_int(page_size):
        raise ValueError("page_size must be a positive integer")

    source_set = frozenset(sources)
    result = _retrieve_unvalidated(
        query,
        kb_index=kb_index,
        locale=locale,
        sources=source_set,
        viewer_group_ids=viewer_access.group_ids,
        product_id=product_id,
        query_vector=query_vector,
        similarity_floor=similarity_floor,
        semantic_k=semantic_k,
        num_candidates=num_candidates,
        rank_window_size=rank_window_size,
        locale_composition=locale_composition,
        page_size=page_size,
        privileged=viewer_access.privileged,
        default_operator=default_operator,
        minimum_should_match=minimum_should_match,
        strict=strict,
        excluded_family_ids=excluded_family_ids,
    )
    return authorize_candidates(
        result,
        viewer_access=viewer_access,
        locale=locale,
        product_id=product_id,
        page_size=page_size,
    )


def authorize_candidates(
    result: RetrievalResult[UnvalidatedCandidate],
    *,
    viewer_access: ViewerAccess,
    locale: str,
    product_id: int | None,
    page_size: int,
) -> RetrievalResult[AuthorizedCandidate]:
    """Apply the primary-database authorization boundary to indexed candidates."""
    started = perf_counter()
    passages = [
        candidate.evidence
        for candidate in result.candidates
        if isinstance(candidate.evidence, RetrievalPassage)
    ]
    family_by_source_id = {}
    displays = {}
    if passages:
        source_ids: set[int] = set()
        family_ids: set[int] = set()
        for passage in passages:
            source_id = parse_positive_integer_id(passage.object_id)
            family_id = parse_positive_integer_id(passage.family_id.removeprefix("kb:"))
            if source_id is not None and family_id is not None:
                source_ids.add(source_id)
                family_ids.add(family_id)

        display_locales = {locale, ENGLISH_LOCALE}
        documents = content_eligible_documents(Document.objects.using(PRIMARY_DATABASE)).filter(
            Q(id__in=source_ids)
            | Q(id__in=family_ids, locale__in=display_locales)
            | Q(parent_id__in=family_ids, locale__in=display_locales)
        )

        if not viewer_access.privileged:
            access = Q(parent__isnull=True, restrict_to_groups__isnull=True) | Q(
                parent__isnull=False, parent__restrict_to_groups__isnull=True
            )
            if viewer_access.group_ids:
                access |= Q(
                    parent__isnull=True, restrict_to_groups__id__in=viewer_access.group_ids
                ) | Q(
                    parent__isnull=False,
                    parent__restrict_to_groups__id__in=viewer_access.group_ids,
                )
            documents = documents.filter(access)

        if product_id is not None:
            documents = documents.filter(
                Q(parent__isnull=True, products__id=product_id)
                | Q(parent__isnull=False, parent__products__id=product_id)
            )

        for (
            document_id,
            parent_id,
            document_locale,
            title,
            slug,
            summary,
        ) in documents.distinct().values_list(
            "id",
            "parent_id",
            "locale",
            "title",
            "slug",
            "current_revision__summary",
        ):
            family_id = parent_id or document_id
            family_by_source_id[document_id] = family_id
            displays[(family_id, document_locale)] = DisplayDocument(
                document_id,
                document_locale,
                title,
                slug,
                summary,
            )

    authorized = []
    for candidate in result.candidates:
        if isinstance(candidate.evidence, LegacyQuestion):
            authorized.append(
                AuthorizedCandidate(
                    candidate.rank,
                    candidate.score,
                    candidate.family_id,
                    candidate.evidence,
                )
            )
            continue

        passage = candidate.evidence
        source_id = parse_positive_integer_id(passage.object_id)
        if source_id is None:
            continue
        family_id = family_by_source_id.get(source_id)
        if family_id is None or candidate.family_id != f"kb:{family_id}":
            continue
        display = displays.get((family_id, locale)) or displays.get((family_id, ENGLISH_LOCALE))
        if display is not None:
            authorized.append(
                AuthorizedCandidate(
                    candidate.rank,
                    candidate.score,
                    candidate.family_id,
                    AuthorizedPassage(passage, display),
                )
            )

    return RetrievalResult(
        candidates=tuple(authorized[:page_size]),
        approximate_total=result.approximate_total,
        has_more=len(authorized) > page_size or result.has_more,
        mode=result.mode,
        degraded=result.degraded,
        failed_shards=result.failed_shards,
        took_ms=result.took_ms,
        encountered_family_ids=(
            result.encountered_family_ids
            or tuple(candidate.family_id for candidate in result.candidates)
        ),
        family_counts=result.family_counts,
        invalid_hit_count=result.invalid_hit_count,
        authorization_rejection_count=(
            result.authorization_rejection_count + len(result.candidates) - len(authorized)
        ),
        db_ms=round((perf_counter() - started) * 1000) if passages else 0,
    )


def reauthorize_cached_candidates(
    result: RetrievalResult[AuthorizedCandidate],
    *,
    viewer_access: ViewerAccess,
    locale: str,
    product_id: int | None,
) -> RetrievalResult[AuthorizedCandidate]:
    """Recheck cached KB evidence against the primary database before presentation."""
    unvalidated = []
    for candidate in result.candidates:
        evidence = (
            candidate.evidence.passage
            if isinstance(candidate.evidence, AuthorizedPassage)
            else candidate.evidence
        )
        unvalidated.append(
            UnvalidatedCandidate(
                candidate.rank,
                candidate.score,
                candidate.family_id,
                evidence,
            )
        )

    unvalidated_result = RetrievalResult(
        candidates=tuple(unvalidated),
        approximate_total=result.approximate_total,
        has_more=result.has_more,
        mode=result.mode,
        degraded=result.degraded,
        failed_shards=result.failed_shards,
        took_ms=result.took_ms,
        encountered_family_ids=result.encountered_family_ids,
        family_counts=result.family_counts,
        invalid_hit_count=result.invalid_hit_count,
        authorization_rejection_count=result.authorization_rejection_count,
        db_ms=result.db_ms,
    )
    return authorize_candidates(
        unvalidated_result,
        viewer_access=viewer_access,
        locale=locale,
        product_id=product_id,
        page_size=len(unvalidated),
    )
