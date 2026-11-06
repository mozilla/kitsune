import json
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest import mock

from django.conf import settings
from django.test.utils import override_settings
from parameterized import parameterized
from pyquery import PyQuery as pq
from waffle.testutils import override_switch

from kitsune.groups.tests import EnterpriseCompanyFactory
from kitsune.retrieval.access import (
    AuthorizedCandidate,
    AuthorizedPassage,
    DisplayDocument,
    ViewerAccess,
)
from kitsune.retrieval.embeddings import EmbeddingRecipe
from kitsune.retrieval.query import LegacyQuestion, RetrievalPassage, RetrievalResult
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.models import Audience
from kitsune.wiki.tests import AudienceFactory, DocumentFactory

RECIPE = EmbeddingRecipe("fake", "model", 2, "document", "query", "l2")


def _candidate(document, rank=1):
    passage = RetrievalPassage(
        content_type="kb",
        object_id=str(document.id),
        family_id=f"kb:{document.id}",
        locale="en-US",
        position=0,
        heading_path="",
        scope=(),
        text="Passage",
        provenance=frozenset({"lexical"}),
        body_highlight=None,
        summary_highlight=None,
        product_ids=(),
        topic_ids=(),
        category="10",
    )
    display = DisplayDocument(document.id, "en-US", document.title, document.slug, "Summary")
    return AuthorizedCandidate(rank, 0.5, f"kb:{document.id}", AuthorizedPassage(passage, display))


def _question(rank=1):
    question = LegacyQuestion(
        question_id="9",
        family_id="aaq:9",
        locale="en-US",
        title="Question",
        content="Question content",
        updated=datetime.now(UTC),
        is_solved=False,
        num_answers=0,
        num_votes=0,
        provenance=frozenset({"lexical"}),
        highlight=None,
    )
    return AuthorizedCandidate(rank, 0.5, "aaq:9", question)


def _result(*candidates):
    return RetrievalResult(
        candidates=candidates,
        approximate_total=len(candidates),
        has_more=False,
        mode="hybrid",
        degraded=False,
        failed_shards=0,
        took_ms=1,
    )


@contextmanager
def _retrieval(main=(), block=()):
    def fake_retrieve(query, **kwargs):
        return _result(*(block if kwargs.get("restricted_only") else main))

    with (
        override_switch("retrieval-hybrid-search", active=True),
        mock.patch(
            "kitsune.search.hybrid.resolve_read_state", return_value=("retrieval-1", RECIPE, {})
        ),
        mock.patch("kitsune.search.hybrid.similarity_floor_for_meta", return_value=0.8),
        mock.patch(
            "kitsune.search.hybrid.get_cached_query_vector", return_value=([1.0, 0.0], "hit")
        ),
        mock.patch("kitsune.search.hybrid.retrieve", side_effect=fake_retrieve) as retrieve,
    ):
        yield retrieve


class KnowledgeBaseSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        company = EnterpriseCompanyFactory()
        agents_group = GroupFactory()
        staff_group = GroupFactory(name=settings.STAFF_GROUP)
        cls.northwind = AudienceFactory(name="Northwind", is_listed=True, groups=[company.group])
        cls.agents = AudienceFactory(name="Agents", is_listed=True, groups=[agents_group])
        cls.handbook = AudienceFactory(name="Handbook", is_public=True, is_listed=True)
        cls.legacy = AudienceFactory(name="Legacy partners", groups=[agents_group])
        AudienceFactory(
            name="Other company", is_listed=True, groups=[EnterpriseCompanyFactory().group]
        )
        cls.group_ids = {
            "member": (company.group.id,),
            "staff": tuple(sorted((staff_group.id, agents_group.id))),
        }
        cls.viewers = {
            "anonymous": None,
            "nobody": UserFactory(),
            "grouped": UserFactory(groups=[GroupFactory()]),
            "member": UserFactory(groups=[company.group]),
            "agent": UserFactory(groups=[agents_group]),
            "both": UserFactory(groups=[company.group, agents_group]),
            "staff": UserFactory(groups=[staff_group, agents_group]),
        }

    def _search(self, viewer, **params):
        user = self.viewers[viewer]
        if user:
            self.client.force_login(user)
        return self.client.get(reverse("search", locale="en-US"), {"q": "firefox", **params})

    def _json(self, viewer, **params):
        response = self._search(viewer, format="json", **params)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    @parameterized.expand(
        [("unknown", False), ("default", False), ("unlisted", True), ("other_company", True)]
    )
    def test_unreadable_kb_is_an_invalid_search(self, case, private):
        slug = {
            "unknown": "no-such-kb",
            "default": Audience.objects.default().slug,
            "unlisted": self.legacy.slug,
            "other_company": self.northwind.slug,
        }[case]
        with _retrieval() as retrieve:
            json_response = self._search("agent", kb=slug, format="json")
            html_response = self._search("agent", kb=slug)

        retrieve.assert_not_called()
        self.assertEqual(json_response.status_code, 400)
        self.assertEqual(json.loads(json_response.content), {"error": "Invalid search data."})
        self.assertEqual(html_response.status_code, 200)
        doc = pq(html_response.content)
        self.assertFalse(doc("#search-results"))
        self.assertFalse(doc('input[name="kb"]'))
        if private:
            self.assertNotIn(slug.encode(), html_response.content)

    @parameterized.expand([(hybrid_on, w) for hybrid_on in (True, False) for w in (2, 3, 4)])
    def test_scoped_search_stays_in_the_kb(self, hybrid_on, w):
        original = DocumentFactory(audiences=[self.northwind])
        DocumentFactory(parent=original, locale="de")
        DocumentFactory(audiences=[self.handbook])

        with (
            _retrieval() as retrieve,
            override_switch("retrieval-hybrid-search", active=hybrid_on),
            mock.patch(
                "kitsune.search.views.CompoundSearch", side_effect=AssertionError("legacy search")
            ),
        ):
            data = self._json("member", kb=self.northwind.slug, w=w)
            html_response = self._search("member", kb=self.northwind.slug, w=w)

        if hybrid_on:
            # One call per request: no private block beside a scope.
            self.assertEqual(retrieve.call_count, 2)
            for call in retrieve.call_args_list:
                self.assertEqual(call.kwargs["sources"], {"kb"})
                self.assertEqual(set(call.kwargs["included_family_ids"]), {f"kb:{original.id}"})
                self.assertFalse(call.kwargs.get("restricted_only"))
        else:
            retrieve.assert_not_called()
            self.assertEqual(data["knowledge_bases"], [])
        self.assertEqual(data["num_results"], 0)
        self.assertIsNone(data["fallback_results"])
        self.assertEqual(data["kb"], self.northwind.slug)
        self.assertEqual(data["private_block"], [])
        self.assertEqual(html_response.status_code, 200)
        self.assertFalse(pq(html_response.content)(".sumo-card-grid .card"))

    @parameterized.expand(
        [
            ("member", 1, True),
            ("member", 2, True),
            ("staff", 1, True),
            ("anonymous", 1, False),
            ("nobody", 1, False),
            ("grouped", 1, False),
        ]
    )
    def test_private_block_is_excluded_from_the_main_results(self, viewer, page, has_block):
        private = DocumentFactory(audiences=[self.northwind])
        public = DocumentFactory(audiences=[self.handbook])

        with _retrieval(main=(_candidate(public),), block=(_candidate(private),)) as retrieve:
            data = self._json(viewer, page=page)

        main = retrieve.call_args_list[-1].kwargs
        if has_block:
            self.assertEqual(retrieve.call_count, 2)
            block = retrieve.call_args_list[0].kwargs
            self.assertTrue(block["restricted_only"])
            self.assertEqual(block["viewer_access"], ViewerAccess(self.group_ids[viewer]))
            self.assertEqual(block["sources"], {"kb"})
            self.assertEqual((block["page_size"], block["offset"]), (3, 0))
            self.assertEqual(block["query_vector"], main["query_vector"])
            self.assertEqual(main["excluded_family_ids"], (f"kb:{private.id}",))
        else:
            retrieve.assert_called_once()
            self.assertFalse(main.get("excluded_family_ids"))
        self.assertEqual(
            [item["title"] for item in data["private_block"]],
            [private.title] if has_block and page == 1 else [],
        )
        self.assertEqual([item["title"] for item in data["results"]], [public.title])

    def test_total_counts_the_private_block_on_every_page(self):
        private = DocumentFactory(audiences=[self.northwind])
        public = DocumentFactory(audiences=[self.handbook])

        with _retrieval(main=(_candidate(public),), block=(_candidate(private),)):
            totals = [self._json("member", page=page)["num_results"] for page in (1, 2)]

        self.assertEqual(totals, [2, 2])

    @parameterized.expand(
        [
            ("one_kb", [["northwind", "agents"], ["northwind"]], "From Northwind"),
            ("two_kbs", [["northwind"], ["agents"]], "From your knowledge bases"),
            ("unlisted", [["legacy"], ["legacy"]], "From your knowledge bases"),
        ]
    )
    def test_private_block_heading(self, name, audiences, heading):
        kbs = {"northwind": self.northwind, "agents": self.agents, "legacy": self.legacy}
        block = tuple(
            _candidate(DocumentFactory(audiences=[kbs[key] for key in keys]), rank)
            for rank, keys in enumerate(audiences, start=1)
        )
        with _retrieval(block=block):
            data = self._json("both")

        self.assertEqual(data["private_block_heading"], heading)
        self.assertEqual(data["num_results"], len(block))
        self.assertIsNone(data["fallback_results"])
        self.assertEqual(
            [kb["name"] for kb in data["private_block"][0]["knowledge_bases"]],
            sorted(kbs[key].name for key in audiences[0] if key != "legacy"),
        )

    def test_tags_list_only_readable_non_default_kbs(self):
        document = DocumentFactory(
            audiences=[Audience.objects.default(), self.agents, self.northwind, self.handbook]
        )
        with _retrieval(main=(_candidate(document), _question(rank=2))):
            data = self._json("agent")

        article, question = data["results"]
        self.assertEqual(
            article["knowledge_bases"],
            [
                {"slug": self.agents.slug, "name": "Agents", "is_private": True},
                {"slug": self.handbook.slug, "name": "Handbook", "is_private": False},
            ],
        )
        self.assertNotIn("knowledge_bases", question)

    @parameterized.expand(
        [
            ("anonymous", None, ["Handbook"]),
            ("member", None, ["Northwind", "Handbook"]),
            ("staff", None, ["Agents", "Handbook"]),
            ("staff", "northwind", ["Agents", "Northwind", "Handbook"]),
        ]
    )
    def test_filter_lists_the_viewers_kbs_and_the_selected_one(self, viewer, selected, names):
        params = {"kb": self.northwind.slug} if selected else {}
        with _retrieval():
            data = self._json(viewer, **params)

        self.assertEqual([kb["name"] for kb in data["knowledge_bases"]], names)
        self.assertEqual(
            {kb["name"]: kb["is_private"] for kb in data["knowledge_bases"]}.get("Handbook"),
            False,
        )
        self.assertEqual(data["kb"], params.get("kb"))

    def test_results_page_shows_the_filter_block_and_tags(self):
        private = DocumentFactory(audiences=[self.northwind])
        public = DocumentFactory(audiences=[self.handbook])
        with _retrieval(main=(_candidate(public),), block=(_candidate(private),)):
            response = self._search("member", all_products=1)

        doc = pq(response.content)
        self.assertEqual(
            [item.text() for item in doc("#kb-filter li").items()],
            ["All results", "Northwind", "Handbook"],
        )
        self.assertEqual(doc("#kb-filter li.selected").text(), "All results")
        northwind_url = doc("#kb-filter li:nth-child(2) a").attr("href")
        self.assertIn(f"kb={self.northwind.slug}", northwind_url)
        self.assertIn("all_products=1", northwind_url)
        self.assertTrue(doc("#kb-filter li:nth-child(2) svg.kb-lock[aria-label]"))
        self.assertEqual(doc("#private-block h2").text(), "From Northwind")
        self.assertEqual(doc("#private-block a.title").text(), private.title)
        self.assertEqual(doc("#private-block .tag-list li").text(), "Northwind")
        self.assertTrue(doc("#private-block .tag-list li svg.kb-lock[aria-label]"))
        self.assertEqual(doc(".content-box .tag-list li").text(), "Handbook")
        self.assertFalse(doc(".content-box .tag-list li svg"))

    @parameterized.expand(
        [
            ("member", {}, True),
            ("member", {"format": "json"}, True),
            ("member", {"kb": "nope"}, True),
            ("member", {"kb": "nope", "format": "json"}, True),
            ("staff", {}, True),
            ("anonymous", {}, False),
            ("nobody", {"format": "json"}, False),
        ]
    )
    @override_settings(CACHE_MIDDLEWARE_SECONDS=3600, GTM_CONTAINER_ID="GTM-TEST")
    def test_private_access_responses_are_not_cached_referred_or_tracked(
        self, viewer, params, private
    ):
        with _retrieval():
            response = self._search(viewer, **params)

        cache_control = {
            directive.strip() for directive in response.get("Cache-Control", "").split(",")
        }
        self.assertEqual(response.get("Referrer-Policy") == "strict-origin", private)
        self.assertEqual({"private", "no-store"} <= cache_control, private)
        if "format" not in params:
            self.assertEqual("/gtm-snippet." in response.content.decode(), not private)
