from django.conf import settings
from django.core.cache import cache
from django.test.utils import override_settings
from parameterized import parameterized
from pyquery import PyQuery as pq
from waffle.testutils import override_switch

from kitsune.groups.tests import GroupProfileFactory
from kitsune.products.models import HOT_TOPIC_SLUG, ProductSupportConfig
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
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
            doc("#document-list > section > article:first-child > div > h2 > a").text(),
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
            doc("#document-list > section > article:nth-child(2) > div > h2> a").text(),
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
            doc("#document-list > section > article:nth-child(2) > div > h2").text(), docs[0].title
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


_THEMED_SLUG = "themed-product"
_THEMED_BODY = f"body.product-theme--{_THEMED_SLUG}"


class ProductThemeClassTests(TestCase):
    """Pages with a product context carry its theme class; the Enterprise banner carries its own."""

    def setUp(self):
        super().setUp()
        product = ProductFactory(slug=_THEMED_SLUG)
        locale, _ = QuestionLocale.objects.get_or_create(locale=settings.LANGUAGE_CODE)
        ProductSupportConfigFactory(
            product=product,
            is_active=True,
            forum_config=AAQConfigFactory(enabled_locales=[locale]),
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
        )
        self.topic = TopicFactory(products=[product])
        self.document = ApprovedRevisionFactory(
            document__products=[product], document__topics=[self.topic]
        ).document
        self.question = QuestionFactory(product=product, topic=self.topic)
        self.unthemed_document = ApprovedRevisionFactory(document__products=[]).document

        # The base TestCase clears the cache, so the banner check reads this setup.
        enterprise = GroupProfileFactory(slug=settings.ENTERPRISE_GROUP_SLUG)
        ProductSupportConfigFactory(
            product=ProductFactory(slug="firefox-enterprise"),
            is_active=True,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
            zendesk_config=ZendeskConfigFactory(),
        )
        user = UserFactory(groups=[enterprise.group])
        self.client.login(username=user.username, password="testpass")

    @parameterized.expand(
        [
            (
                "product_landing",
                lambda test: reverse("products.product", args=[_THEMED_SLUG]),
                _THEMED_BODY,
            ),
            (
                "topic_of_product",
                lambda test: reverse("products.documents", args=[_THEMED_SLUG, test.topic.slug]),
                _THEMED_BODY,
            ),
            (
                "kb_article",
                lambda test: test.document.get_absolute_url(),
                _THEMED_BODY,
            ),
            (
                "kb_article_without_product",
                lambda test: test.unthemed_document.get_absolute_url(),
                None,
            ),
            (
                "aaq_step",
                lambda test: reverse("questions.aaq_step2", args=[_THEMED_SLUG]),
                _THEMED_BODY,
            ),
            (
                "question_details",
                lambda test: reverse("questions.details", args=[test.question.id]),
                _THEMED_BODY,
            ),
            (
                "topic_without_product",
                lambda test: reverse("products.topic_documents", args=[test.topic.slug]),
                None,
            ),
            (
                "home_banner",
                lambda test: reverse("home"),
                ".enterprise-banner.product-theme--firefox-enterprise",
            ),
            (
                "products_banner",
                lambda test: reverse("products"),
                ".enterprise-banner.product-theme--firefox-enterprise",
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
