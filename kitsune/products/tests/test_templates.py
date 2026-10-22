import json
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext, modify_settings, override_settings
from parameterized import parameterized
from pyquery import PyQuery as pq
from waffle.testutils import override_switch

from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import GroupProfileFactory
from kitsune.products.models import HOT_TOPIC_SLUG, CuratedBlock, ProductSupportConfig, Topic
from kitsune.products.tests import (
    CuratedBlockFactory,
    CuratedBlockItemFactory,
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    TopicFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.models import QuestionLocale
from kitsune.questions.tests import AAQConfigFactory, QuestionFactory
from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory
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


class ProfessionalSupportTestCase(TestCase):
    """Sets up a product with professional support and an organization that has it."""

    def setUp(self):
        self.product = ProductFactory(slug=settings.ENTERPRISE_GROUP_SLUG)
        locale, _ = QuestionLocale.objects.get_or_create(locale=settings.LANGUAGE_CODE)
        self.config = ProductSupportConfigFactory(
            product=self.product,
            forum_config=AAQConfigFactory(enabled_locales=[locale]),
            zendesk_config=ZendeskConfigFactory(),
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            group_default_support_type=ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
        )
        self.root = GroupProfileFactory(slug=settings.ENTERPRISE_GROUP_SLUG)
        self.org = self.add_org(self.config, "acme")
        self.team = GroupProfile.objects.add_child(
            self.org, create_kwargs={"group": GroupFactory(), "slug": "acme-it"}
        )
        self.url = reverse("products.product", args=[self.product.slug])

    def add_org(self, config, slug):
        """Add a company under the enterprise group and make it a support organization."""
        org = GroupProfile.objects.add_child(
            self.root, create_kwargs={"group": GroupFactory(), "slug": slug}
        )
        SupportOrganizationFactory(config=config, group=org.group).full_clean()
        return org

    def login_member(self, group_profile=None):
        user = UserFactory()
        user.groups.add((group_profile or self.team).group)
        self.client.login(username=user.username, password="testpass")


class EnterpriseGetSupportTests(ProfessionalSupportTestCase):
    """Users with professional support for the product get the Get help section;
    everyone else gets a banner."""

    def test_member_sees_get_support(self):
        TopicFactory(slug="getting-started", products=[self.product])
        self.login_member()

        doc = pq(self.client.get(self.url, follow=True).content)

        self.assertEqual(0, len(doc(".support-callouts")))
        section = doc(".get-support.support-callouts--top")
        self.assertEqual(3, len(section(".get-support--item")))
        # Each card's title is its link.
        links = [pq(a).attr("href") for a in section(".get-support--title a")]
        self.assertEqual(
            links,
            [
                reverse("questions.aaq_step3", kwargs={"product_slug": self.product.slug})
                + f"?support_type={ProductSupportConfig.SUPPORT_TYPE_ZENDESK}",
                reverse("products.documents", args=[self.product.slug, "getting-started"]),
                reverse("groups.profile", args=[self.org.slug]),
            ],
        )
        self.assertEqual("Get help", section("h2").text())

    def test_direct_company_member_sees_get_support(self):
        self.login_member(self.org)

        doc = pq(self.client.get(self.url, follow=True).content)

        section = doc(".get-support.support-callouts--top")
        self.assertEqual(1, len(section))
        links = [pq(a).attr("href") for a in section(".get-support--title a")]
        self.assertIn(reverse("groups.profile", args=[self.org.slug]), links)

    def test_get_started_card_hidden_without_topic(self):
        self.login_member()

        doc = pq(self.client.get(self.url, follow=True).content)

        section = doc(".get-support.support-callouts--top")
        self.assertEqual(2, len(section(".get-support--item")))
        self.assertEqual(0, len(section(".get-support--badge.is-getting-started")))

    def test_member_without_zendesk_sees_still_need_help(self):
        self.config.zendesk_config = None
        self.config.save()
        self.login_member()

        doc = pq(self.client.get(self.url, follow=True).content)

        self.assertEqual(0, len(doc(".get-support")))
        self.assertIn("Still need help?", doc(".support-callouts--top .card--title").text())

    def test_member_on_other_product_is_sent_to_their_support_page(self):
        other = ProductFactory()
        locale, _ = QuestionLocale.objects.get_or_create(locale=settings.LANGUAGE_CODE)
        ProductSupportConfigFactory(
            product=other,
            forum_config=AAQConfigFactory(enabled_locales=[locale]),
            zendesk_config=None,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
        )
        self.login_member()

        url = reverse("products.product", args=[other.slug])
        doc = pq(self.client.get(url, follow=True).content)

        self.assertEqual(0, len(doc(".get-support")))
        self.assertEqual(1, len(doc(".support-callouts--top")))
        self.assertEqual(1, len(doc(".support-callouts--bottom")))
        # The product's own support stays available alongside the pro banner.
        middle = doc(
            ".support-callouts:not(.support-callouts--top):not(.support-callouts--bottom)"
        )
        self.assertEqual(1, len(middle))
        self.assertEqual("Still need help?", middle(".card--title").text())
        banner = doc(".support-callouts--top")
        self.assertEqual("Firefox Professional Support", banner(".card--title").text())
        self.assertEqual(
            "Visit your organization’s dedicated support page to contact our team and access "
            "your support services.",
            banner(".card--desc").text(),
        )
        button = banner("a.sumo-button")
        self.assertEqual("Access Support", button.text())
        self.assertEqual(self.url, button.attr("href"))

    def test_member_on_product_without_support_config_is_sent_to_their_support_page(self):
        other = ProductFactory()
        self.login_member()

        url = reverse("products.product", args=[other.slug])
        doc = pq(self.client.get(url, follow=True).content)

        banner = doc(".support-callouts--top")
        self.assertEqual("Firefox Professional Support", banner(".card--title").text())
        self.assertEqual(self.url, banner("a.sumo-button").attr("href"))

    def test_logged_out_sees_talk_to_an_expert(self):
        doc = pq(self.client.get(self.url, follow=True).content)

        self.assertEqual(0, len(doc(".get-support")))
        banner = doc(".support-callouts--top")
        self.assertEqual("Need dedicated support?", banner(".card--title").text())
        self.assertIn(
            "firefox.com/en-US/browsers/enterprise/contact/", banner("a.sumo-button").attr("href")
        )

    def test_non_member_sees_still_need_help(self):
        user = UserFactory()
        self.client.login(username=user.username, password="testpass")

        doc = pq(self.client.get(self.url, follow=True).content)

        self.assertEqual(0, len(doc(".get-support")))
        banner = doc(".support-callouts--top")
        self.assertIn("Still need help?", banner(".card--title").text())
        self.assertEqual(
            reverse("questions.aaq_step3", kwargs={"product_slug": self.product.slug}),
            banner("a.sumo-button").attr("href"),
        )


class ProfessionalSupportBannerTests(ProfessionalSupportTestCase):
    """The home page and the product list point members to their support page."""

    pages = ("home", "products")

    def test_member_sees_banner(self):
        self.login_member()

        for page in self.pages:
            with self.subTest(page=page):
                doc = pq(self.client.get(reverse(page), follow=True).content)

                banner = doc(".support-callouts")
                self.assertEqual(1, len(banner))
                self.assertEqual("Firefox Professional Support", banner(".card--title").text())
                self.assertEqual(self.url, banner("a.sumo-button").attr("href"))

    def test_non_member_sees_no_banner(self):
        user = UserFactory()
        self.client.login(username=user.username, password="testpass")

        for page in self.pages:
            with self.subTest(page=page):
                doc = pq(self.client.get(reverse(page), follow=True).content)
                self.assertEqual(0, len(doc(".support-callouts")))

    def test_logged_out_sees_no_banner(self):
        for page in self.pages:
            with self.subTest(page=page):
                doc = pq(self.client.get(reverse(page), follow=True).content)
                self.assertEqual(0, len(doc(".support-callouts")))


class ProMastheadTests(ProfessionalSupportTestCase):
    """The enterprise page always gets the pro support masthead; other products only for
    users with professional support for them."""

    masthead = ".home-search-section.pro-support-masthead"

    def test_enterprise_page_always_has_it(self):
        doc = pq(self.client.get(self.url, follow=True).content)
        self.assertEqual(1, len(doc(self.masthead)))

    def test_other_product_without_pro_support_does_not(self):
        other = ProductFactory()
        self.login_member()

        doc = pq(
            self.client.get(reverse("products.product", args=[other.slug]), follow=True).content
        )
        self.assertEqual(0, len(doc(self.masthead)))

    def test_other_product_with_pro_support_does(self):
        other = ProductFactory()
        config = ProductSupportConfigFactory(product=other, zendesk_config=ZendeskConfigFactory())
        self.login_member(self.add_org(config, "globex"))

        doc = pq(
            self.client.get(reverse("products.product", args=[other.slug]), follow=True).content
        )
        self.assertEqual(1, len(doc(self.masthead)))


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
