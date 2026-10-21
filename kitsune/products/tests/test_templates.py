from django.conf import settings
from django.core.cache import cache
from django.test.utils import override_settings
from pyquery import PyQuery as pq
from waffle.testutils import override_switch

from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import GroupProfileFactory
from kitsune.products.models import HOT_TOPIC_SLUG, ProductSupportConfig
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    TopicFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.models import QuestionLocale
from kitsune.questions.tests import AAQConfigFactory
from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory
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
