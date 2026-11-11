import re
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db import connection
from django.test.client import RequestFactory
from django.test.utils import CaptureQueriesContext, override_settings
from django.utils import timezone
from parameterized import parameterized
from pyquery import PyQuery as pq

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.config import DEFAULT_AUDIENCE_SLUG
from kitsune.wiki.models import Audience, AudienceFeaturedDocument, Document
from kitsune.wiki.templatetags.jinja_helpers import kb_menu
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    AudienceFactory,
    DocumentFactory,
    TranslatedRevisionFactory,
)

PER_REQUEST_VALUES = re.compile(rb"nonce=\"[^\"]*\"|name='csrfmiddlewaretoken' value='[^']*'")


def _article(knowledge_base, title, created=None, **document_kwargs):
    revision = ApprovedRevisionFactory(
        document__title=title,
        document__audiences=[knowledge_base],
        created=created or timezone.now(),
        **{f"document__{name}": value for name, value in document_kwargs.items()},
    )
    return revision.document


def _texts(doc, selector):
    return [element.text_content().strip() for element in doc(selector)]


def _locked_names(doc, item_selector, name_selector):
    return [
        pq(item).find(name_selector).text()
        for item in doc(item_selector)
        if pq(item).find(".kb-lock")
    ]


class KnowledgeBasePageTests(TestCase):
    def setUp(self):
        self.company = GroupFactory()
        self.member = UserFactory(groups=[self.company])
        self.kb = AudienceFactory(
            name="Northwind Health",
            is_listed=True,
            groups=[self.company],
            description="Guides for the Northwind IT team.",
        )

    def _get(self, knowledge_base=None, locale=None, **params):
        url = reverse(
            "wiki.knowledge_base", args=[(knowledge_base or self.kb).slug], locale=locale
        )
        return self.client.get(url, params)

    @parameterized.expand([("anonymous",), ("outsider",)])
    def test_hidden_knowledge_bases_are_not_found_alike(self, viewer):
        unlisted = AudienceFactory(is_public=True)
        Audience.objects.default()
        if viewer == "outsider":
            self.client.force_login(UserFactory())

        responses = [
            self.client.get(reverse("wiki.knowledge_base", args=[slug]))
            for slug in ("no-such-kb", DEFAULT_AUDIENCE_SLUG, unlisted.slug, self.kb.slug)
        ]

        self.assertEqual({response.status_code for response in responses}, {404})
        self.assertEqual(
            len({PER_REQUEST_VALUES.sub(b"", response.content) for response in responses}), 1
        )
        self.assertNotIn(self.kb.name, responses[-1].content.decode())

    def test_reader_sees_the_sections(self):
        product = ProductFactory()
        deployment = TopicFactory(title="Deployment", products=[product])
        start = _article(self.kb, "Deploying Firefox", topics=[deployment], products=[product])
        moved = _article(self.kb, "Moved elsewhere")
        draft = DocumentFactory(title="Unapproved draft", audiences=[self.kb])
        for order, document in enumerate((moved, start, draft)):
            AudienceFeaturedDocument.objects.create(
                audience=self.kb, document=document, order=order
            )
        moved.audiences.set([AudienceFactory()])
        now = timezone.now()
        for days in range(6):
            _article(self.kb, f"Update {days}", created=now - timedelta(days=days + 1))
        self.client.force_login(self.member)

        response = self._get()

        self.assertEqual(response.status_code, 200)
        doc = pq(response.content)
        self.assertEqual(doc(".kb-hero h1").text(), "Northwind Health")
        self.assertEqual(doc(".kb-hero--description").text(), "Guides for the Northwind IT team.")
        search = doc("form#kb-search")
        self.assertTrue(search.attr("action").endswith("/search/"))
        self.assertEqual(search.find("input[name=kb]").val(), self.kb.slug)
        self.assertEqual(_texts(doc, "#kb-start-here .card--title"), ["Deploying Firefox"])
        self.assertEqual(_texts(doc, "#kb-topics .card--title"), ["Deployment"])
        self.assertIn(f"topic={deployment.slug}", doc("#kb-topics .card--title a").attr("href"))
        self.assertEqual(
            _texts(doc, "#kb-recent .kb-recent--title"),
            ["Deploying Firefox", "Update 0", "Update 1", "Update 2", "Update 3"],
        )

    @parameterized.expand(
        [
            ("public", True, "anonymous", "Open to everyone."),
            ("member", False, "member", "Only members can see these articles."),
            ("staff", False, "staff", "Only members can see these articles."),
        ]
    )
    @override_settings(GTM_CONTAINER_ID="GTM-TEST")
    def test_privacy_line_referrer_and_analytics(self, name, is_public, viewer, privacy):
        Audience.objects.filter(pk=self.kb.pk).update(is_public=is_public)
        if viewer == "member":
            self.client.force_login(self.member)
        elif viewer == "staff":
            self.client.force_login(UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]))

        response = self._get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(pq(response.content)(".kb-privacy").text(), privacy)
        self.assertEqual("/gtm-snippet." in response.content.decode(), is_public)
        if is_public:
            self.assertNotEqual(response.headers["Referrer-Policy"], "strict-origin")
        else:
            self.assertEqual(response.headers["Referrer-Policy"], "strict-origin")
            self.assertIn("no-store", response.headers["Cache-Control"])

    @parameterized.expand([("without_url", "", 0), ("with_url", "https://example.com/help", 1)])
    def test_support_ribbon_needs_a_url(self, name, support_url, expected):
        Audience.objects.filter(pk=self.kb.pk).update(
            support_url=support_url,
            support_text="Your plan includes help.",
            support_link_text="Contact us",
        )
        self.client.force_login(self.member)

        ribbon = pq(self._get().content)("#kb-support")

        self.assertEqual(len(ribbon), expected)
        if expected:
            self.assertEqual(ribbon.find("a").attr("href"), support_url)
            self.assertEqual(ribbon.find("a").text(), "Contact us")

    @parameterized.expand(
        [
            ("topic", "first", ["Alpha", "Bravo"]),
            ("page", "1", ["Alpha", "Bravo", "Charlie"]),
        ]
    )
    def test_list_mode(self, param, value, expected):
        first, second = TopicFactory(slug="first"), TopicFactory(slug="second")
        _article(self.kb, "Bravo", topics=[first])
        _article(self.kb, "Charlie", topics=[second])
        _article(self.kb, "Alpha", topics=[first])
        self.client.force_login(self.member)

        doc = pq(self._get(**{param: value}).content)

        self.assertEqual(_texts(doc, "#kb-articles .topic-doc-list--title"), expected)
        self.assertEqual(len(doc("#kb-topics")), 0)

    @parameterized.expand([("one_product", 1), ("two_products", 2)])
    def test_product_filter_needs_two_products(self, name, count):
        products = [ProductFactory() for _ in range(count)]
        topic = TopicFactory(products=products)
        for index, product in enumerate(products):
            _article(self.kb, f"Article {index}", products=[product], topics=[topic])
        self.client.force_login(self.member)

        doc = pq(self._get().content)
        self.assertEqual(len(doc("#kb-product-filter")), int(count > 1))

        if count > 1:
            doc = pq(self._get(page="1", product=products[1].slug).content)
            self.assertEqual(_texts(doc, "#kb-articles .topic-doc-list--title"), ["Article 1"])

            doc = pq(self._get(product=products[1].slug).content)
            self.assertEqual(_texts(doc, "#kb-recent .kb-recent--title"), ["Article 1"])

    @parameterized.expand(
        [
            ("unknown_topic", {"topic": "missing"}, 404),
            ("unknown_product", {"product": "missing"}, 404),
            ("second_page", {"topic": "first", "product": "tools", "page": "2"}, 200),
        ]
    )
    def test_list_filters(self, name, params, status):
        topic, product = TopicFactory(slug="first"), ProductFactory(slug="tools")
        for title in ("Alpha", "Bravo"):
            _article(self.kb, title, topics=[topic], products=[product])
        self.client.force_login(self.member)

        with mock.patch("kitsune.wiki.kb_views.DOCUMENTS_PER_PAGE", 1):
            response = self._get(**params)

        self.assertEqual(response.status_code, status)
        if status == 200:
            doc = pq(response.content)
            self.assertEqual(_texts(doc, "#kb-articles .topic-doc-list--title"), ["Bravo"])
            links = [link.get("href") for link in doc(".pagination a")]
            self.assertTrue(links)
            for link in links:
                self.assertIn("topic=first", link)
                self.assertIn("product=tools", link)

    def test_queries_do_not_grow_with_articles(self):
        topic = TopicFactory()
        _article(self.kb, "First", topics=[topic])
        self.client.force_login(self.member)
        self._get()

        def count_queries():
            with CaptureQueriesContext(connection) as queries:
                self._get()
            return len(queries)

        before = count_queries()
        for index in range(4):
            _article(self.kb, f"More {index}", topics=[topic])

        self.assertEqual(count_queries(), before)

    def test_article_list_loads_only_its_page(self):
        for index in range(5):
            _article(self.kb, f"Article {index}")
        self.client.force_login(self.member)

        with (
            mock.patch("kitsune.wiki.kb_views.DOCUMENTS_PER_PAGE", 2),
            mock.patch.object(Document, "from_db", wraps=Document.from_db) as from_db,
        ):
            response = self._get(page=2)

        self.assertEqual(
            _texts(pq(response.content), "#kb-articles .topic-doc-list--title"),
            ["Article 2", "Article 3"],
        )
        self.assertEqual(from_db.call_count, 2)

    def test_request_locale_with_english_fallback(self):
        public = AudienceFactory(is_public=True, is_listed=True)
        translated = _article(public, "In English")
        TranslatedRevisionFactory(
            document__parent=translated,
            document__locale="de",
            document__title="Auf Deutsch",
            based_on=translated.current_revision,
        )
        _article(public, "Only in English")
        AudienceFeaturedDocument.objects.create(audience=public, document=translated)

        doc = pq(self._get(public, locale="de").content)

        self.assertEqual(_texts(doc, "#kb-start-here .card--title"), ["Auf Deutsch"])
        self.assertEqual(
            sorted(_texts(doc, "#kb-recent .kb-recent--title")), ["Auf Deutsch", "Only in English"]
        )

    def test_empty_knowledge_base(self):
        self.client.force_login(self.member)

        doc = pq(self._get().content)

        self.assertEqual(len(doc("#kb-empty")), 1)
        self.assertEqual(len(doc("#kb-start-here, #kb-topics, #kb-recent")), 0)


class KnowledgeBaseDirectoryTests(TestCase):
    @parameterized.expand(
        [
            ("anonymous", [("Open to everyone", ["Alpha", "Zulu"])], []),
            (
                "member",
                [
                    ("Your knowledge bases", ["Northwind"]),
                    ("Open to everyone", ["Alpha", "Zulu"]),
                ],
                ["Northwind"],
            ),
            ("staff", [("Open to everyone", ["Alpha", "Zulu"])], []),
        ]
    )
    def test_groups_by_visibility(self, viewer, expected_groups, locked):
        company = GroupFactory()
        AudienceFactory(name="Zulu", is_public=True, is_listed=True)
        AudienceFactory(name="Alpha", is_public=True, is_listed=True)
        AudienceFactory(name="Northwind", is_listed=True, groups=[company])
        AudienceFactory(name="Another company", is_listed=True, groups=[GroupFactory()])
        AudienceFactory(name="Not listed", is_public=True)
        if viewer == "member":
            self.client.force_login(UserFactory(groups=[company]))
        elif viewer == "staff":
            self.client.force_login(UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]))

        response = self.client.get(reverse("wiki.knowledge_bases"))

        doc = pq(response.content)
        self.assertEqual(
            [
                (group("h2").text(), _texts(group, ".card--title"))
                for group in doc("#kb-directory .kb-directory--group").items()
            ],
            expected_groups,
        )
        self.assertEqual(_locked_names(doc, "#kb-directory .card--kb", ".card--title"), locked)
        content = response.content.decode()
        self.assertNotIn("Another company", content)
        self.assertNotIn("Not listed", content)

    @parameterized.expand([("anonymous", False), ("staff", False), ("member", True)])
    @override_settings(CACHE_MIDDLEWARE_SECONDS=3600, GTM_CONTAINER_ID="GTM-TEST")
    def test_listing_private_knowledge_bases_is_not_cached_referred_or_tracked(
        self, viewer, private
    ):
        company = GroupFactory()
        AudienceFactory(name="Open", is_public=True, is_listed=True)
        AudienceFactory(name="Northwind", is_listed=True, groups=[company])
        if viewer == "member":
            self.client.force_login(UserFactory(groups=[company]))
        elif viewer == "staff":
            self.client.force_login(UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]))

        response = self.client.get(reverse("wiki.knowledge_bases"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual("/gtm-snippet." in response.content.decode(), not private)
        self.assertEqual(response.headers.get("Referrer-Policy") == "strict-origin", private)
        cache_control = {
            directive.strip() for directive in response.headers.get("Cache-Control", "").split(",")
        }
        self.assertEqual({"private", "no-store"} <= cache_control, private)

    def test_empty_state(self):
        AudienceFactory(name="Another company", is_listed=True, groups=[GroupFactory()])

        response = self.client.get(reverse("wiki.knowledge_bases"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(pq(response.content)("#kb-directory-empty")), 1)
        self.assertNotIn("Another company", response.content.decode())


class KnowledgeBaseMenuTests(TestCase):
    def setUp(self):
        self.company = GroupFactory()
        AudienceFactory(name="Other company", is_listed=True, groups=[GroupFactory()])
        AudienceFactory(name="Not listed", is_public=True)

    def _menu_page(self):
        response = self.client.get(reverse("products"))
        return response.content.decode(), pq(response.content)("#kb-menu")

    def _anonymous_menu_names(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        return [entry.name for _, entries in kb_menu(request) for entry in entries]

    def test_absent_without_listed_knowledge_bases(self):
        content, menu = self._menu_page()

        self.assertEqual(len(menu), 0)
        self.assertNotIn("Other company", content)

    @parameterized.expand(
        [
            ("anonymous", [("Open to everyone", ["Open"])], []),
            (
                "member",
                [("Your knowledge bases", ["Member"]), ("Open to everyone", ["Open"])],
                ["Member"],
            ),
            ("staff", [("Open to everyone", ["Open"])], []),
        ]
    )
    def test_lists_what_the_viewer_may_list(self, viewer, expected_groups, locked):
        AudienceFactory(name="Open", is_public=True, is_listed=True)
        AudienceFactory(name="Member", is_listed=True, groups=[self.company])
        if viewer == "member":
            self.client.force_login(UserFactory(groups=[self.company]))
        elif viewer == "staff":
            self.client.force_login(UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]))

        content, menu = self._menu_page()

        self.assertEqual(
            menu.closest(".mzp-c-menu-category").children(".mzp-c-menu-title").text(),
            "Explore Help Articles",
        )
        self.assertEqual(
            [
                (heading.text(), _texts(heading.next(), ".kb-menu--name"))
                for heading in menu(".kb-menu--heading").items()
            ],
            expected_groups,
        )
        self.assertEqual(_locked_names(menu, ".kb-menu--link", ".kb-menu--name"), locked)
        self.assertNotIn("Other company", content)
        self.assertNotIn("Not listed", content)

    @parameterized.expand(
        [
            ("audience_save", ["After"]),
            ("audience_delete", []),
        ]
    )
    def test_changes_retire_the_cached_listing(self, change, expected):
        knowledge_base = AudienceFactory(name="Before", is_public=True, is_listed=True)
        self._anonymous_menu_names()
        Audience.objects.filter(pk=knowledge_base.pk).update(name="After")
        self.assertEqual(self._anonymous_menu_names(), ["Before"])
        knowledge_base.refresh_from_db()

        with self.captureOnCommitCallbacks(execute=True):
            {
                "audience_save": knowledge_base.save,
                "audience_delete": knowledge_base.delete,
            }[change]()

        self.assertEqual(self._anonymous_menu_names(), expected)

    def test_a_fill_that_raced_a_change_is_never_read(self):
        knowledge_base = AudienceFactory(name="Turning private", is_public=True, is_listed=True)
        fill = cache.set

        def change_then_fill(*args, **kwargs):
            knowledge_base.is_public = False
            with self.captureOnCommitCallbacks(execute=True):
                knowledge_base.save()
            fill(*args, **kwargs)

        with mock.patch.object(cache, "set", side_effect=change_then_fill):
            self._anonymous_menu_names()

        self.assertEqual(self._anonymous_menu_names(), [])
