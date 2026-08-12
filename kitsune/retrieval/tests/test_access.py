from dataclasses import replace
from datetime import UTC, datetime
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from kitsune.products.tests import ProductFactory
from kitsune.retrieval.access import (
    AuthorizedPassage,
    ViewerAccess,
    retrieve,
    viewer_access_for,
)
from kitsune.retrieval.query import (
    LegacyQuestion,
    RetrievalPassage,
    RetrievalResult,
    UnvalidatedCandidate,
)
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.models import Document
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


def _approved(**kwargs):
    document = DocumentFactory(**kwargs)
    ApprovedRevisionFactory(document=document)
    return Document.objects.get(pk=document.pk)


def _passage(document, *, family_id=None):
    family_id = family_id or document.parent_id or document.id
    return RetrievalPassage(
        content_type="kb",
        object_id=str(document.id),
        family_id=f"kb:{family_id}",
        locale=document.locale,
        position=0,
        heading_path="",
        scope=(),
        text="Indexed passage",
        provenance=frozenset({"semantic"}),
        body_highlight=None,
        summary_highlight=None,
        product_ids=(),
        topic_ids=(),
        category=str(document.category),
    )


def _question():
    return LegacyQuestion(
        question_id="7",
        family_id="aaq:7",
        locale="en-US",
        title="Question",
        content="Question content",
        updated=datetime.now(UTC),
        is_solved=True,
        num_answers=1,
        num_votes=2,
        provenance=frozenset({"lexical"}),
        highlight=None,
    )


def _result(*evidence):
    return RetrievalResult(
        candidates=tuple(
            UnvalidatedCandidate(rank, 1 / rank, item.family_id, item)
            for rank, item in enumerate(evidence, start=1)
        ),
        approximate_total=len(evidence),
        has_more=False,
        mode="hybrid",
        degraded=False,
        failed_shards=0,
        took_ms=3,
    )


def _retrieve(
    result,
    *,
    viewer_access=ViewerAccess(),
    locale="en-US",
    product_id=None,
    page_size=10,
    offset=0,
):
    sources = (
        {"aaq"}
        if all(isinstance(item.evidence, LegacyQuestion) for item in result.candidates)
        else {"kb"}
    )
    with mock.patch(
        "kitsune.retrieval.access._retrieve_unvalidated", return_value=result
    ) as search:
        authorized = retrieve(
            "firefox",
            viewer_access=viewer_access,
            kb_index=None if sources == {"aaq"} else "retrieval-read",
            locale=locale,
            sources=sources,
            product_id=product_id,
            query_vector=None,
            similarity_floor=None,
            semantic_k=20,
            num_candidates=40,
            rank_window_size=50,
            locale_composition="combined",
            page_size=page_size,
            authorization_overfetch=5,
            offset=offset,
            max_offset=20,
        )
    return authorized, search


class ViewerAccessTests(TestCase):
    def test_anonymous_and_superuser_need_no_membership_query(self):
        superuser = UserFactory(is_superuser=True)

        with self.assertNumQueries(0):
            self.assertEqual(viewer_access_for(AnonymousUser()), ViewerAccess())
            self.assertEqual(viewer_access_for(superuser), ViewerAccess(privileged=True))

    def test_one_membership_query_resolves_groups_or_staff_bypass(self):
        first = GroupFactory()
        second = GroupFactory()
        user = UserFactory(groups=[second, first])
        staff = UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)])

        with self.assertNumQueries(1):
            access = viewer_access_for(user)
        self.assertEqual(access, ViewerAccess(tuple(sorted((first.id, second.id)))))

        with self.assertNumQueries(1):
            self.assertEqual(viewer_access_for(staff), ViewerAccess(privileged=True))


class CandidateAuthorizationTests(TestCase):
    def test_one_query_authorizes_sources_and_prefers_requested_display_locale(self):
        product = ProductFactory()
        original = _approved(locale="en-US", products=[product])
        translation = _approved(parent=original, locale="de", title="Deutsch")
        another_match = _approved(locale="en-US", products=[product])
        wrong_product = _approved(locale="en-US")
        indexed = _result(
            _passage(original),
            _passage(another_match),
            _passage(wrong_product),
        )

        # A newer revision is freshness drift, not an authorization failure.
        ApprovedRevisionFactory(document=original, summary="Current summary")

        with self.assertNumQueries(1):
            result, search = _retrieve(
                indexed,
                locale="de",
                product_id=product.id,
                page_size=1,
            )

        self.assertEqual(len(result.candidates), 1)
        self.assertTrue(result.has_more)
        self.assertEqual(search.call_args.kwargs["page_size"], 6)
        evidence = result.candidates[0].evidence
        self.assertIsInstance(evidence, AuthorizedPassage)
        self.assertEqual(evidence.display.document_id, translation.id)
        self.assertEqual(evidence.display.title, "Deutsch")

    def test_an_eligible_sibling_does_not_rescue_an_ineligible_source(self):
        original = _approved(locale="en-US")
        stale_translation = _approved(parent=original, locale="de")
        no_revision = DocumentFactory(locale="en-US")
        deleted = _approved(locale="en-US")
        deleted_passage = _passage(deleted)
        deleted.delete()
        Document.objects.filter(pk=stale_translation.pk).update(is_archived=True)

        indexed = _result(
            _passage(stale_translation),
            _passage(no_revision),
            deleted_passage,
            replace(_passage(no_revision), object_id="²", family_id="kb:²"),
        )
        with self.assertNumQueries(1):
            result, _ = _retrieve(indexed)

        self.assertEqual(result.candidates, ())
        self.assertEqual(result.approximate_total, 4)

    def test_authorizes_a_prefix_before_selecting_a_later_page(self):
        wrong_product = _approved(locale="en-US")
        product = ProductFactory()
        first = _approved(locale="en-US", products=[product])
        second = _approved(locale="en-US", products=[product])
        third = _approved(locale="en-US", products=[product])

        with self.assertNumQueries(1):
            result, search = _retrieve(
                _result(
                    _passage(wrong_product),
                    _passage(first),
                    _passage(second),
                    _passage(third),
                ),
                product_id=product.id,
                page_size=1,
                offset=1,
            )

        self.assertEqual(result.candidates[0].family_id, f"kb:{second.id}")
        self.assertTrue(result.has_more)
        self.assertEqual(search.call_args.kwargs["offset"], 0)
        self.assertEqual(search.call_args.kwargs["page_size"], 7)

    def test_raw_next_page_is_not_hidden_by_authorization_overfetch(self):
        first = _approved(locale="en-US")
        second = _approved(locale="en-US")
        indexed = replace(_result(_passage(first), _passage(second)), has_more=True)

        result, _ = _retrieve(indexed, page_size=2)

        self.assertEqual(len(result.candidates), 2)
        self.assertTrue(result.has_more)

    def test_group_access_and_privileged_bypass_use_the_same_policy_query(self):
        allowed_group = GroupFactory()
        restricted = _approved(restrict_to_groups=[allowed_group])
        indexed = _result(_passage(restricted))

        denied, _ = _retrieve(indexed)
        allowed, _ = _retrieve(
            indexed,
            viewer_access=ViewerAccess((allowed_group.id,)),
            locale="de",
        )
        privileged, search = _retrieve(indexed, viewer_access=ViewerAccess(privileged=True))

        self.assertEqual(denied.candidates, ())
        self.assertEqual(len(allowed.candidates), 1)
        allowed_evidence = allowed.candidates[0].evidence
        self.assertIsInstance(allowed_evidence, AuthorizedPassage)
        self.assertEqual(allowed_evidence.display.locale, "en-US")
        self.assertEqual(len(privileged.candidates), 1)
        self.assertTrue(search.call_args.kwargs["privileged"])

    def test_aaq_needs_no_database_authorization_query(self):
        with self.assertNumQueries(0):
            result, search = _retrieve(_result(_question()), viewer_access=ViewerAccess((7,)))

        self.assertIsInstance(result.candidates[0].evidence, LegacyQuestion)
        self.assertEqual(search.call_args.kwargs["viewer_group_ids"], (7,))
        self.assertEqual(search.call_args.kwargs["page_size"], 10)
