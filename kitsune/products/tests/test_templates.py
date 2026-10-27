import json
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext, modify_settings, override_settings
from django.utils import timezone
from parameterized import parameterized
from pyquery import PyQuery as pq
from waffle.testutils import override_switch

from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.products.models import HOT_TOPIC_SLUG, CuratedBlock, ProductSupportConfig, Topic
from kitsune.products.tests import (
    CuratedBlockFactory,
    CuratedBlockItemFactory,
    ProductFactory,
    ProductSupportConfigFactory,
    SupportContractFactory,
    SupportCoverageFactory,
    TopicFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.models import QuestionLocale
from kitsune.questions.tests import AAQConfigFactory, QuestionFactory
from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory, HelpfulVoteFactory

Kind = CuratedBlock.Kind
Variant = CuratedBlock.Variant


class ProductViewsTestCase(ElasticTestCase):
    search_tests = True

    def test_products(self):
        """Verify that /products page renders products."""
        # Create some products.
        locale, _ = QuestionLocale.objects.get_or_create(locale=settings.LANGUAGE_CODE)
        for i in range(3):
            ProductSupportConfigFactory(
                is_active=True,
                product=ProductFactory(visible=True),
                forum_config=AAQConfigFactory(enabled_locales=[locale]),
                default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            )

        # GET the products page and verify the content.
        r = self.client.get(reverse("products"), follow=True)
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(3, len(doc(".card--product")))

    def test_product_landing(self):
        """Verify that /products/<slug> page renders topics."""
        # Create a product.
        p = ProductFactory()
        locale, _ = QuestionLocale.objects.get_or_create(locale=settings.LANGUAGE_CODE)
        ProductSupportConfigFactory(
            product=p,
            is_active=True,
            forum_config=AAQConfigFactory(enabled_locales=[locale]),
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
        )

        # Create some topics.
        TopicFactory(slug=HOT_TOPIC_SLUG, products=[p], visible=True)
        topics = TopicFactory.create_batch(11, products=[p], visible=True)

        # Create a document and assign the product and 10 topics.
        d = DocumentFactory(products=[p], topics=topics[:10])
        ApprovedRevisionFactory(document=d)

        # GET the product landing page and verify the content.
        url = reverse("products.product", args=[p.slug])
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(10, len(doc("div.card--topic")))
        self.assertEqual(p.slug, doc("#support-search input[name=product]").attr["value"])

    def test_firefox_product_landing(self):
        """Verify that there is no firefox button visible at header in the firefox landing page"""
        p = ProductFactory(slug="firefox")
        url = reverse("products.product", args=[p.slug])
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(1, doc(".firefox-download-button.hidden").length)

    def test_document_listing(self):
        """Verify /products/<product slug>/<topic slug> renders articles."""
        # Create a topic and product.
        p = ProductFactory()
        t1 = TopicFactory(products=[p])
        # Create 3 documents with the topic and product and one without.
        ApprovedRevisionFactory.create_batch(3, document__products=[p], document__topics=[t1])
        ApprovedRevisionFactory()

        # GET the page and verify the content.
        url = reverse("products.documents", args=[p.slug, t1.slug])
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(3, len(doc("#document-list > section > article")))
        self.assertEqual(p.slug, doc("#support-search input[name=product]").attr["value"])

    def test_document_listing_order(self):
        """Verify documents are sorted by display_order and number of helpful votes."""
        # Create topic, product and documents.
        p = ProductFactory()
        t = TopicFactory(products=[p])
        docs = []
        # FIXME: Can't we do this with create_batch and build the document
        # in the approvedrevisionfactory
        for i in range(3):
            doc = DocumentFactory(products=[p], topics=[t])
            ApprovedRevisionFactory(document=doc)
            docs.append(doc)

        # Add a lower display order to the second document. It should be first now.
        docs[1].display_order = 0
        docs[1].save()
        url = reverse("products.documents", args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(
            doc("#document-list > section > article:first-child > div > h3 > a").text(),
            docs[1].title,
        )

        # Add a helpful vote to the third document. It should be second now.
        rev = docs[2].current_revision
        HelpfulVoteFactory(revision=rev, helpful=True)
        docs[2].save()  # Votes don't trigger a reindex.
        cache.clear()  # documents_for() is cached
        url = reverse("products.documents", args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(
            doc("#document-list > section > article:nth-child(2) > div > h3 > a").text(),
            docs[2].title,
        )

        # Add 2 helpful votes the first document. It should be second now.
        rev = docs[0].current_revision
        HelpfulVoteFactory(revision=rev, helpful=True)
        HelpfulVoteFactory(revision=rev, helpful=True)
        docs[0].save()  # Votes don't trigger a reindex.
        cache.clear()  # documents_for() is cached
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(
            doc("#document-list > section > article:nth-child(2) > div > h3").text(), docs[0].title
        )

    def test_subtopics(self):
        """Verifies subtopics appear on document listing page."""
        # Create a topic and product.
        p = ProductFactory()
        t = TopicFactory(products=[p], visible=True)

        # Create a documents with the topic and product
        doc = DocumentFactory(products=[p], topics=[t])
        ApprovedRevisionFactory(document=doc)

        # GET the page and verify no subtopics yet.
        url = reverse("products.documents", args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        pqdoc = pq(r.content)
        self.assertEqual(1, len(pqdoc(".subtopics>li")))

        # Create a subtopic, it still shouldn't show up because no
        # articles are assigned.
        subtopic = TopicFactory(parent=t, products=[p], visible=True)
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        pqdoc = pq(r.content)
        self.assertEqual(1, len(pqdoc(".subtopics>li")))

        # Add a document to the subtopic, now it should appear.
        doc.topics.add(subtopic)

        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        pqdoc = pq(r.content)
        self.assertEqual(2, len(pqdoc(".subtopics>li")))


class TopicPageHeaderTests(TestCase):
    """The product strip and the compact topic header."""

    def setUp(self):
        super().setUp()
        self.product = ProductFactory()
        self.topic = TopicFactory(products=[self.product])
        ApprovedRevisionFactory(document__products=[self.product], document__topics=[self.topic])

    def get_page(self, name, *args):
        return pq(self.client.get(reverse(name, args=args), follow=True).content)

    def test_product_page_has_strip_and_topic_tile(self):
        doc = self.get_page("products.documents", self.product.slug, self.topic.slug)

        link = doc(".product-strip a.product-strip--product")
        self.assertEqual(reverse("products.product", args=[self.product.slug]), link.attr("href"))
        self.assertEqual(self.product.title, link.text())
        self.assertEqual(self.topic.image_url, doc(".topic-header--tile img").attr("src"))

    def test_cross_product_page_has_tile_without_strip(self):
        doc = self.get_page("products.topic_documents", self.topic.slug)

        self.assertEqual(0, len(doc(".product-strip")))
        self.assertEqual(1, len(doc(".topic-header--tile")))

    def test_no_tile_without_topic_image(self):
        self.topic.image = None
        self.topic.save()

        doc = self.get_page("products.documents", self.product.slug, self.topic.slug)

        self.assertEqual(0, len(doc(".topic-header--tile")))


class TopicPageCuratedBlockTests(TestCase):
    """The curated blocks of a product topic page and their effect on the article list."""

    def setUp(self):
        super().setUp()
        self.product = ProductFactory()
        self.topic = TopicFactory(products=[self.product])
        self.articles = [self.add_article(self.topic) for _ in range(6)]

    def add_article(self, topic):
        revision = ApprovedRevisionFactory(
            document__products=[self.product], document__topics=[topic]
        )
        return revision.document

    def add_block(self, kind, variant, items=None, topic=None, **fields):
        if items is None and kind == Kind.ARTICLES:
            items = self.articles[:2]
        elif items is None and kind == Kind.QUESTIONS:
            items = [QuestionFactory(product=self.product, topic=self.topic) for _ in range(2)]
        block = CuratedBlockFactory(
            product=self.product, topic=topic or self.topic, kind=kind, variant=variant, **fields
        )
        field = "question" if kind == Kind.QUESTIONS else "document"
        for position, target in enumerate(items or []):
            CuratedBlockItemFactory(block=block, position=position, **{field: target})
        return block

    def page_url(self, subtopic=None, locale="en-US"):
        if subtopic:
            args = [self.product.slug, self.topic.slug, subtopic.slug]
            return reverse("products.subtopics", args=args, locale=locale)
        return reverse(
            "products.documents", args=[self.product.slug, self.topic.slug], locale=locale
        )

    def get_page(self, url):
        return pq(self.client.get(url, follow=True).content)

    def test_blocks_render_in_a_fixed_order_above_the_list(self):
        self.add_block(Kind.QUESTIONS, Variant.MANUAL)
        self.add_block(Kind.ARTICLES, Variant.NUMBERED)
        self.add_block(Kind.CALLOUT, Variant.GOOD_TO_KNOW)

        doc = self.get_page(self.page_url())

        rendered = doc("#document-list > .curated-block, #document-list > .list-toolbar")
        self.assertEqual(
            [
                "curated-block is-callout is-good-to-know",
                "curated-block is-articles is-numbered",
                "curated-block is-questions is-manual",
                "list-toolbar",
            ],
            [pq(element).attr("class") for element in rendered],
        )

    @parameterized.expand(
        [
            (Kind.CALLOUT, Variant.GOOD_TO_KNOW, "Good to know"),
            (Kind.CALLOUT, Variant.IMPORTANT, "Important"),
            (Kind.ARTICLES, Variant.NUMBERED, "Start here"),
            (Kind.ARTICLES, Variant.FEATURED, "Featured Articles"),
            (Kind.QUESTIONS, Variant.MANUAL, "Popular in the forums"),
        ]
    )
    def test_heading_follows_the_variant(self, kind, variant, heading):
        self.add_block(kind, variant)

        doc = self.get_page(self.page_url())

        self.assertEqual(heading, doc(".curated-block--heading").text())

    @parameterized.expand(
        [
            ("plain", "Back up your bookmarks first."),
            ("percent_and_markup", "Save 50% of the <b>time</b> & {more}"),
        ]
    )
    def test_callout_message_is_shown_as_text(self, _name, message):
        self.add_block(Kind.CALLOUT, Variant.IMPORTANT, message=message)

        doc = self.get_page(self.page_url())

        self.assertEqual(message, doc(".curated-block--message").text())
        self.assertEqual(0, len(doc(".curated-block--message b")))

    def test_translated_callout_message_with_a_percent_sign_renders(self):
        self.add_block(Kind.CALLOUT, Variant.IMPORTANT, message="Save time")
        translated = "Spare 50% der <b>Zeit</b>"

        with mock.patch(
            "kitsune.products.templatetags.jinja_helpers.pgettext", return_value=translated
        ):
            doc = self.get_page(self.page_url())

        self.assertEqual(translated, doc(".curated-block--message").text())
        self.assertEqual(0, len(doc(".curated-block--message b")))

    @parameterized.expand(
        [("parent_tab", False, "good-to-know"), ("subtopic_tab", True, "important")]
    )
    def test_subtopic_tab_inherits_blocks_and_overrides_per_kind(
        self, _name, on_subtopic, variant
    ):
        subtopic = TopicFactory(parent=self.topic, products=[self.product])
        self.add_block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, message="Parent note")
        self.add_block(Kind.ARTICLES, Variant.NUMBERED)
        self.add_block(Kind.CALLOUT, Variant.IMPORTANT, topic=subtopic, message="Subtopic note")

        doc = self.get_page(self.page_url(subtopic if on_subtopic else None))

        self.assertEqual(
            [f"curated-block is-callout is-{variant}", "curated-block is-articles is-numbered"],
            [pq(block).attr("class") for block in doc(".curated-block")],
        )
        self.assertEqual(
            "Subtopic note" if on_subtopic else "Parent note",
            doc(".curated-block--message").text(),
        )

    def test_no_blocks_renders_nothing_and_the_full_list(self):
        doc = self.get_page(self.page_url())

        self.assertEqual(0, len(doc(".curated-block")))
        self.assertEqual(6, len(doc(".topic-doc-list--item")))
        self.assertEqual("All articles", doc(".list-toolbar--heading").text())

    @parameterized.expand(
        [
            ("cross_product", "products.topic_documents", False),
            ("topic_filtered_by_product", "products.topic_product_documents", True),
        ]
    )
    def test_cross_product_pages_render_no_blocks(self, _name, url_name, with_product):
        self.add_block(Kind.CALLOUT, Variant.GOOD_TO_KNOW)
        self.add_block(Kind.ARTICLES, Variant.NUMBERED)
        args = [self.topic.slug] + ([self.product.slug] if with_product else [])

        doc = self.get_page(reverse(url_name, args=args))

        self.assertEqual(0, len(doc(".curated-block")))
        self.assertEqual(6, len(doc(".topic-doc-list--item")))
        self.assertEqual("All articles", doc(".list-toolbar--heading").text())

    @parameterized.expand([("topic_tab", False), ("subtopic_tab", True)])
    def test_card_articles_leave_the_list_but_callout_links_stay(self, _name, on_subtopic):
        viewed = self.topic
        if on_subtopic:
            viewed = TopicFactory(parent=self.topic, products=[self.product])
            for article in self.articles:
                article.topics.add(viewed)
        self.add_block(Kind.ARTICLES, Variant.NUMBERED, items=self.articles[:4])
        self.add_block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, items=self.articles[4:5])

        doc = self.get_page(self.page_url(viewed if on_subtopic else None))

        self.assertEqual(
            [article.get_absolute_url() for article in self.articles[:4]],
            [pq(link).attr("href") for link in doc(".is-articles .curated-block--title a")],
        )
        self.assertCountEqual(
            [article.get_absolute_url() for article in self.articles[4:]],
            [pq(link).attr("href") for link in doc(".topic-doc-list--title a")],
        )
        self.assertEqual(f"More in {viewed.title}", doc(".list-toolbar--heading").text())
        self.assertEqual("2", doc(".list-toolbar--count").text())

    @parameterized.expand([("no_articles", False, 1), ("every_article_is_a_card", True, 0)])
    def test_empty_state_shows_only_when_the_topic_has_no_articles(
        self, _name, all_are_cards, expected
    ):
        topic = self.topic if all_are_cards else TopicFactory(products=[self.product])
        if all_are_cards:
            self.add_block(Kind.ARTICLES, Variant.NUMBERED, items=self.articles)

        doc = self.get_page(reverse("products.documents", args=[self.product.slug, topic.slug]))

        self.assertEqual(expected, len(doc(".topic-doc-list-empty")))
        self.assertEqual(0, len(doc(".list-toolbar")))

    def test_card_articles_leave_both_lists_on_a_localized_page(self):
        translated = [self.articles[0], self.articles[4]]
        translations = {}
        for article in translated:
            translation = DocumentFactory(parent=article, locale="de")
            ApprovedRevisionFactory(document=translation, based_on=article.current_revision)
            translations[article.pk] = translation
        self.add_block(Kind.ARTICLES, Variant.NUMBERED, items=self.articles[:4])

        doc = self.get_page(self.page_url(locale="de"))

        cards = doc(".is-articles .curated-block--card")
        self.assertEqual(
            [translations[self.articles[0].pk].title] + [a.title for a in self.articles[1:4]],
            [pq(card).find(".curated-block--title").text() for card in cards],
        )
        label = doc(".topic-doc-list-heading").text()
        self.assertEqual(
            ["", label, label, label],
            [pq(card).find(".curated-block--lang").text() for card in cards],
        )
        self.assertEqual(
            [translations[self.articles[4].pk].title],
            [pq(title).text() for title in doc("[data-topic-list] .topic-doc-list--title")],
        )
        self.assertEqual(
            [self.articles[5].title],
            [pq(title).text() for title in doc(".is-compact .topic-doc-list--title")],
        )
        self.assertTrue(
            all(pq(link).attr("href").startswith("/de/") for link in doc(".curated-block a"))
        )

    @parameterized.expand(
        [
            (
                "numbered",
                Kind.ARTICLES,
                Variant.NUMBERED,
                ".curated-block--card a",
                "curated.kb-article",
            ),
            (
                "featured",
                Kind.ARTICLES,
                Variant.FEATURED,
                ".curated-block--card a",
                "curated.kb-article",
            ),
            (
                "callout",
                Kind.CALLOUT,
                Variant.IMPORTANT,
                ".curated-block--link",
                "curated.kb-article",
            ),
            (
                "questions",
                Kind.QUESTIONS,
                Variant.MANUAL,
                ".curated-block--card a",
                "curated.question",
            ),
        ]
    )
    def test_curated_links_report_kind_and_position(
        self, link_kind, kind, variant, selector, link_name
    ):
        items = self.articles[:2] if kind == Kind.CALLOUT else None
        self.add_block(kind, variant, items=items)

        doc = self.get_page(self.page_url())

        events = [json.loads(pq(link).attr("data-event-parameters")) for link in doc(selector)]
        self.assertEqual(
            [
                {"link_name": link_name, "link_detail": f"{link_kind}:{position}"}
                for position in (1, 2)
            ],
            events,
        )


class TopicPageListRowTests(TestCase):
    """The meta line under each article in the topic list."""

    DATE = r"[A-Z][a-z]{2} \d{1,2}, \d{4}"

    def setUp(self):
        super().setUp()
        self.product = ProductFactory(title="Primary")
        self.other_product = ProductFactory(title="Secondary")
        self.topic = TopicFactory(products=[self.product, self.other_product])
        ApprovedRevisionFactory(
            document__title="Single revision",
            document__products=[self.product],
            document__topics=[self.topic],
        )
        shared = ApprovedRevisionFactory(
            document__title="Shared and edited",
            document__products=[self.product, self.other_product],
            document__topics=[self.topic],
        )
        ApprovedRevisionFactory(document=shared.document)

    def meta_by_title(self, name, *args):
        page = pq(self.client.get(reverse(name, args=args), follow=True).content)
        rows = (pq(row) for row in page(".topic-doc-list--item"))
        return {
            row.find(".topic-doc-list--title").text(): row.find(".topic-doc-list--meta").text()
            for row in rows
        }

    def test_product_page_meta_names_only_other_products(self):
        meta = self.meta_by_title("products.documents", self.product.slug, self.topic.slug)

        self.assertRegex(meta["Single revision"], rf"^Created {self.DATE}$")
        self.assertRegex(meta["Shared and edited"], rf"^Updated {self.DATE} · Also for Secondary$")

    def test_cross_product_page_meta_lists_product_titles(self):
        meta = self.meta_by_title("products.topic_documents", self.topic.slug)

        self.assertRegex(meta["Single revision"], rf"^Created {self.DATE} · Primary$")
        self.assertRegex(meta["Shared and edited"], rf"^Updated {self.DATE} · Primary, Secondary$")

    # django-silk (USE_DJANGO_SILK) issues its own queries per captured query.
    @modify_settings(MIDDLEWARE={"remove": "silk.middleware.SilkyMiddleware"})
    def test_query_count_does_not_grow_with_the_article_count(self):
        url = reverse("products.documents", args=[self.product.slug, self.topic.slug])

        def count_queries():
            cache.clear()
            with CaptureQueriesContext(connection) as queries:
                self.client.get(url, follow=True)
            return len(queries)

        before = count_queries()
        for _ in range(3):
            ApprovedRevisionFactory(
                document__products=[self.product],
                document__topics=[self.topic],
            )

        self.assertEqual(count_queries(), before)


class TopicPageSortLabelTests(TestCase):
    """The label of the default sort option follows the order the server uses."""

    @parameterized.expand(
        [
            (Topic.ArticleOrdering.DEFAULT, False, "Most helpful"),
            (Topic.ArticleOrdering.NEWEST, False, "Newest"),
            (Topic.ArticleOrdering.NEWEST, True, "Newest"),
        ]
    )
    def test_default_sort_option(self, ordering, on_subtopic, label):
        product = ProductFactory()
        if on_subtopic:
            topic = TopicFactory(products=[product])
            viewed = TopicFactory(parent=topic, products=[product], article_ordering=ordering)
            url = reverse("products.subtopics", args=[product.slug, topic.slug, viewed.slug])
        else:
            viewed = TopicFactory(products=[product], article_ordering=ordering)
            url = reverse("products.documents", args=[product.slug, viewed.slug])
        ApprovedRevisionFactory(document__products=[product], document__topics=[viewed])

        doc = pq(self.client.get(url, follow=True).content)

        self.assertEqual(label, doc('#list-sort option[value="server"]').text())


class ProfessionalSupportPresentationTests(TestCase):
    """Product pages and the professional support banner present each persona's support."""

    sales_url = (
        "https://www.firefox.com/en-US/browsers/enterprise/contact/?utm_source=sumo-announcement"
    )

    def setUp(self):
        today = timezone.localdate()
        current = {"starts_on": today - timedelta(days=1), "ends_on": today + timedelta(days=1)}
        locale, _ = QuestionLocale.objects.get_or_create(locale=settings.LANGUAGE_CODE)
        self.enterprise = ProductFactory(slug=settings.FIREFOX_ENTERPRISE_PRODUCT_SLUG)
        ProductSupportConfigFactory(
            product=self.enterprise,
            forum_config=AAQConfigFactory(enabled_locales=[locale]),
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
        )
        self.vpn = ProductFactory()
        ProductSupportConfigFactory(
            product=self.vpn, zendesk_config=ZendeskConfigFactory(), subscription_only=True
        )
        self.unconfigured = ProductFactory()
        TopicFactory(slug="getting-started", products=[self.unconfigured])

        self.company = EnterpriseCompanyFactory()
        contract = SupportContractFactory(company=self.company, **current)
        for product in (self.vpn, self.unconfigured):
            SupportCoverageFactory(contract=contract, product=product)
        self.enterprise_company = EnterpriseCompanyFactory()
        SupportCoverageFactory(
            product=self.enterprise,
            contract=SupportContractFactory(company=self.enterprise_company, **current),
        )
        self.expired_company = EnterpriseCompanyFactory()
        SupportCoverageFactory(
            product=self.vpn,
            contract=SupportContractFactory(
                company=self.expired_company,
                starts_on=today - timedelta(days=30),
                ends_on=today - timedelta(days=1),
            ),
        )

    def user(self, group=None, *, subscribed=False):
        user = UserFactory()
        if group:
            user.groups.add(group.group)
        if subscribed:
            user.profile.products.add(self.vpn)
        return user

    def blocks(self, doc):
        """Summarize the page's support blocks in order; bottom copies repeat the top ones."""
        blocks = []
        shown = doc(".support-callouts, .get-support").not_(".support-callouts--bottom")
        for block in shown.items():
            if block.has_class("get-support"):
                titles = block(".get-support--title a").items()
                links = [(a.text(), a.attr("href")) for a in titles]
                branded = "Firefox Professional Support" in block.text()
                blocks.append((block("h2").text(), links, branded))
            else:
                button = block("a.sumo-button")
                blocks.append((block(".card--title").text(), button.text(), button.attr("href")))
        return blocks

    def analytics_events(self, doc):
        """Return the parameters analytics.js would send for each tracked element."""
        events = []
        for element in doc("[data-event-name]").items():
            parameters = json.loads(element.attr("data-event-parameters") or "{}")
            href = element.attr("href")
            if element.attr("data-event-name") == "link_click" and href is not None:
                parameters.setdefault("link_url", href)
            events.append(json.dumps(parameters))
        return events

    def step3(self, product):
        return reverse("questions.aaq_step3", args=[product.slug])

    def banner(self, company):
        return (
            "Your company’s support",
            "Access Support",
            reverse("groups.profile", args=[company.slug]) + "#your-support",
        )

    def section(self, product, company, *, branded=False, get_started=False):
        links = [("Contact support", self.step3(product))]
        if get_started:
            url = reverse("products.documents", args=[product.slug, "getting-started"])
            links.append(("Get started", url))
        links.append(("Manage your account", reverse("groups.profile", args=[company.slug])))
        return ("Get help", links, branded)

    def test_presentation_per_persona(self):
        forum = ("Still need help?", "Ask the Community", self.step3(self.enterprise))
        product_ticket = ("Still need help?", "Contact Support", self.step3(self.vpn))
        sales = ("Need dedicated support?", "Talk to an Expert", self.sales_url)
        uncovered = {
            self.enterprise: (True, [forum]),
            self.vpn: (False, []),
            self.unconfigured: (False, []),
        }
        subscriber = {**uncovered, self.vpn: (False, [product_ticket])}
        covered = {
            self.enterprise: (True, [self.banner(self.company), forum]),
            self.vpn: (True, [self.section(self.vpn, self.company)]),
            self.unconfigured: (
                True,
                [self.section(self.unconfigured, self.company, get_started=True)],
            ),
        }
        enterprise_banner = self.banner(self.enterprise_company)
        enterprise_covered = {
            self.enterprise: (
                True,
                [self.section(self.enterprise, self.enterprise_company, branded=True)],
            ),
            self.vpn: (False, [enterprise_banner]),
            self.unconfigured: (False, [enterprise_banner]),
        }
        leader = self.user()
        self.company.leaders.add(leader)
        company_slugs = [
            company.slug
            for company in (self.company, self.enterprise_company, self.expired_company)
        ]

        company_banner = [self.banner(self.company)]
        for persona, user, pages, banner in (
            ("anonymous", None, {**uncovered, self.enterprise: (True, [sales])}, []),
            ("non-member", self.user(), uncovered, []),
            ("company member", self.user(self.company), covered, company_banner),
            (
                "department member",
                self.user(DepartmentFactory(company=self.company)),
                covered,
                company_banner,
            ),
            ("root member", self.user(self.company.get_parent()), uncovered, []),
            ("company leader", leader, uncovered, []),
            ("individual subscriber", self.user(subscribed=True), subscriber, []),
            (
                "both entitlements",
                self.user(self.company, subscribed=True),
                covered,
                company_banner,
            ),
            ("expired coverage", self.user(self.expired_company, subscribed=True), subscriber, []),
            (
                "other product coverage",
                self.user(self.enterprise_company),
                enterprise_covered,
                [enterprise_banner],
            ),
        ):
            if user:
                self.client.force_login(user)
            else:
                self.client.logout()
            expected = {
                reverse("products.product", args=[product.slug]): presentation
                for product, presentation in pages.items()
            }
            expected.update({reverse(page): (False, banner) for page in ("home", "products")})
            for url, presentation in expected.items():
                with self.subTest(persona=persona, url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    doc = pq(response.content)
                    self.assertEqual(
                        (bool(doc(".home-search-section.pro-support-masthead")), self.blocks(doc)),
                        presentation,
                    )
                    leaked = [
                        event
                        for event in self.analytics_events(doc)
                        if any(slug in event for slug in company_slugs)
                    ]
                    self.assertEqual(leaked, [])


_MZLA_SLUGS = ["thunderbird", "thunderbird-android"]
_MATOMO_MARKER = "data-matomo-site-id"


@override_switch("matomo-mzla", active=True)
@override_settings(MATOMO_MZLA_PRODUCT_SLUGS=_MZLA_SLUGS)
class MatomoMzlaProductLandingTests(TestCase):
    """Matomo snippet appears on Thunderbird product landing and not on Firefox."""

    def test_matomo_present_for_mzla_product(self):
        p = ProductFactory(slug="thunderbird")
        url = reverse("products.product", args=[p.slug])
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        self.assertContains(r, _MATOMO_MARKER)

    @override_switch("matomo-mzla", active=False)
    def test_matomo_absent_when_switch_inactive(self):
        p = ProductFactory(slug="thunderbird")
        url = reverse("products.product", args=[p.slug])
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        self.assertNotContains(r, _MATOMO_MARKER)

    def test_matomo_absent_for_non_mzla_product(self):
        p = ProductFactory(slug="firefox")
        url = reverse("products.product", args=[p.slug])
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        self.assertNotContains(r, _MATOMO_MARKER)

    @override_settings(MATOMO_MZLA_SITE_ID="")
    def test_matomo_absent_when_site_id_empty(self):
        p = ProductFactory(slug="thunderbird")
        url = reverse("products.product", args=[p.slug])
        r = self.client.get(url, follow=True)
        self.assertEqual(200, r.status_code)
        self.assertNotContains(r, _MATOMO_MARKER)


_ENTERPRISE_SLUG = "firefox-enterprise"
_ENTERPRISE_BODY = "body.product-theme--enterprise"


class ProductThemeClassTests(TestCase):
    """Enterprise pages carry the Enterprise theme class."""

    def setUp(self):
        super().setUp()
        # Ordered first, so an article without a product falls back to Enterprise.
        enterprise = ProductFactory(slug=_ENTERPRISE_SLUG, display_order=-1)
        ProductSupportConfigFactory(
            product=enterprise,
            is_active=True,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
            zendesk_config=ZendeskConfigFactory(),
        )
        self.topic = TopicFactory(products=[enterprise])
        self.document = ApprovedRevisionFactory(
            document__products=[enterprise], document__topics=[self.topic]
        ).document
        self.question = QuestionFactory(product=enterprise, topic=self.topic)
        self.unthemed_document = ApprovedRevisionFactory(document__products=[]).document
        self.other_product = ProductFactory()

        # The AAQ step needs a signed-in user.
        group = GroupProfileFactory(slug=settings.ENTERPRISE_GROUP_SLUG)
        user = UserFactory(groups=[group.group])
        self.client.login(username=user.username, password="testpass")

    @parameterized.expand(
        [
            (
                "product_landing",
                lambda test: reverse("products.product", args=[_ENTERPRISE_SLUG]),
                _ENTERPRISE_BODY,
            ),
            (
                "topic_of_product",
                lambda test: reverse(
                    "products.documents", args=[_ENTERPRISE_SLUG, test.topic.slug]
                ),
                _ENTERPRISE_BODY,
            ),
            (
                "kb_article",
                lambda test: test.document.get_absolute_url(),
                _ENTERPRISE_BODY,
            ),
            (
                "kb_article_without_product",
                lambda test: test.unthemed_document.get_absolute_url(),
                None,
            ),
            (
                "aaq_step",
                lambda test: reverse("questions.aaq_step2", args=[_ENTERPRISE_SLUG]),
                _ENTERPRISE_BODY,
            ),
            (
                "question_details",
                lambda test: reverse("questions.details", args=[test.question.id]),
                _ENTERPRISE_BODY,
            ),
            (
                "topic_without_product",
                lambda test: reverse("products.topic_documents", args=[test.topic.slug]),
                None,
            ),
            (
                "other_product_landing",
                lambda test: reverse("products.product", args=[test.other_product.slug]),
                None,
            ),
        ]
    )
    def test_product_theme_class(self, _name, url, themed_selector):
        response = self.client.get(url(self), follow=True)
        self.assertEqual(200, response.status_code)
        themed = pq(response.content)('[class*="product-theme--"]')
        if themed_selector is None:
            self.assertEqual(0, len(themed))
        else:
            self.assertEqual(1, len(themed))
            self.assertTrue(themed.is_(themed_selector))
