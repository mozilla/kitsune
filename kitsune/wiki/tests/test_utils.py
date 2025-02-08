from datetime import date, timedelta
from unittest import mock

from django.test.utils import override_settings
from requests.exceptions import HTTPError

from kitsune.dashboards import LAST_7_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DocumentFactory,
    RedirectRevisionFactory,
    RevisionFactory,
    TemplateDocumentFactory,
    TranslatedRevisionFactory,
)
from kitsune.wiki.utils import (
    active_contributors,
    generate_short_url,
    get_featured_articles,
    num_active_contributors,
)


class ActiveContributorsTestCase(TestCase):
    def setUp(self):
        super(ActiveContributorsTestCase, self).setUp()

        start_date = date.today() - timedelta(days=10)
        self.start_date = start_date
        before_start = start_date - timedelta(days=1)

        # Create some revisions to test with.

        # 3 'en-US' contributors:
        d = DocumentFactory(locale="en-US")
        u = UserFactory()
        self.user = u
        RevisionFactory(document=d, is_approved=True, reviewer=u)
        RevisionFactory(document=d, creator=u)

        self.product = ProductFactory()
        RevisionFactory(created=start_date, document__products=[self.product])

        # Add one that shouldn't count:
        self.en_us_old = RevisionFactory(document=d, created=before_start)

        # 4 'es' contributors:
        d = DocumentFactory(locale="es")
        RevisionFactory(document=d, is_approved=True, reviewer=u)
        RevisionFactory(document=d, creator=u, reviewer=UserFactory())
        RevisionFactory(document=d, created=start_date)
        RevisionFactory(document=d)
        # Add one that shouldn't count:
        self.es_old = RevisionFactory(document=d, created=before_start)

    def test_active_contributors(self):
        """Test the active_contributors util method."""
        start_date = self.start_date

        en_us_contributors = active_contributors(from_date=start_date, locale="en-US")
        es_contributors = active_contributors(from_date=start_date, locale="es")
        all_contributors = active_contributors(from_date=start_date)

        # Verify results!
        self.assertEqual(3, len(en_us_contributors))
        assert self.user in en_us_contributors
        assert self.en_us_old.creator not in en_us_contributors

        self.assertEqual(4, len(es_contributors))
        assert self.user in es_contributors
        assert self.es_old.creator not in es_contributors

        self.assertEqual(6, len(all_contributors))
        assert self.user in all_contributors
        assert self.en_us_old.creator not in all_contributors
        assert self.es_old.creator not in all_contributors

    def test_num_active_contributors(self):
        """Test the num_active_contributors util method."""
        start_date = self.start_date

        self.assertEqual(3, num_active_contributors(from_date=start_date, locale="en-US"))
        self.assertEqual(4, num_active_contributors(from_date=start_date, locale="es"))
        self.assertEqual(6, num_active_contributors(from_date=start_date))
        self.assertEqual(1, num_active_contributors(from_date=start_date, product=self.product))
        self.assertEqual(
            1, num_active_contributors(from_date=start_date, locale="en-US", product=self.product)
        )
        self.assertEqual(
            0, num_active_contributors(from_date=start_date, locale="es", product=self.product)
        )


@override_settings(BITLY_ACCESS_TOKEN="access_token")
class GenerateShortUrlTestCase(TestCase):
    def setUp(self):
        self.test_url = "https://support.mozilla.org/en-US/kb/update-firefox-latest-version"

    @mock.patch("kitsune.wiki.utils.requests.post")
    def test_generate_short_url_200(self, mock_requests):
        """Tests a valid 200 response for generate_short_url method."""
        mock_json = mock.Mock()
        mock_json.json.return_value = {"status_code": 200, "link": "http://mzl.la/LFolSf"}
        mock_requests.return_value = mock_json
        self.assertEqual("http://mzl.la/LFolSf", generate_short_url(self.test_url))

    @mock.patch("kitsune.wiki.utils.requests.post")
    def test_generate_short_url_ratelimited_response(self, mock_requests):
        """Tests a valid 419 response for generate_short_url method."""
        mock_response = mock.Mock(ok=False, status_code=419)
        mock_response.raise_for_status.side_effect = HTTPError()
        mock_requests.return_value = mock_response
        self.assertRaises(HTTPError, generate_short_url, self.test_url)


class FeaturedArticlesTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.product1 = product1 = ProductFactory()
        self.product2 = product2 = ProductFactory()
        self.topic1 = topic1 = TopicFactory(products=[product1])
        self.topic2 = topic2 = TopicFactory(products=[product1, product2])
        topic3 = TopicFactory(products=[product2])
        # Create a variety of documents.
        # These will have a current revision.
        self.d1 = d1 = ApprovedRevisionFactory(
            document__products=[product1], document__topics=[topic1]
        ).document
        self.d2 = d2 = ApprovedRevisionFactory(
            document__products=[product1], document__topics=[topic1, topic2]
        ).document
        ApprovedRevisionFactory(
            document__products=[product1, product2], document__topics=[topic2]
        ).document
        ApprovedRevisionFactory(
            document__products=[product2], document__topics=[topic2, topic3]
        ).document
        # These will not have a current revision.
        d3 = RevisionFactory().document
        d4 = RevisionFactory().document
        d5 = RevisionFactory().document
        # This will be a redirect.
        d6 = RedirectRevisionFactory().document
        # These will be archived.
        d7 = ApprovedRevisionFactory(document__is_archived=True).document
        d8 = ApprovedRevisionFactory(document__is_archived=True).document
        # These will be templates.
        d9 = TemplateDocumentFactory()
        ApprovedRevisionFactory(document=d9)
        d10 = TemplateDocumentFactory()
        ApprovedRevisionFactory(document=d10)

        # German documents.
        # These will have a current revision.
        self.de1 = de1 = TranslatedRevisionFactory(
            document__locale="de",
            document__parent__products=[product1],
            document__parent__topics=[topic1, topic2],
        ).document
        self.de2 = de2 = TranslatedRevisionFactory(
            document__locale="de",
            document__parent__products=[product2],
            document__parent__topics=[topic2, topic3],
        ).document
        TranslatedRevisionFactory(
            document__locale="de",
            document__parent__products=[product1, product2],
            document__parent__topics=[topic2],
        ).document
        TranslatedRevisionFactory(
            document__locale="de",
            document__parent__products=[product2],
            document__parent__topics=[topic2, topic3],
        ).document
        # These will not have a current revision.
        de3 = DocumentFactory(locale="de", parent=DocumentFactory())
        de4 = DocumentFactory(locale="de", parent=DocumentFactory())
        de5 = DocumentFactory(locale="de", parent=DocumentFactory())
        # These will be redirects.
        de6 = RedirectRevisionFactory(
            document__locale="de", document__parent=DocumentFactory()
        ).document
        # These will be archived.
        de7 = TranslatedRevisionFactory(
            document__locale="de", document__is_archived=True, document__parent__is_archived=True
        ).document
        de8 = TranslatedRevisionFactory(
            document__locale="de", document__is_archived=True, document__parent__is_archived=True
        ).document
        # These will be templates.
        de9 = TemplateDocumentFactory(locale="de", parent=TemplateDocumentFactory())
        ApprovedRevisionFactory(document=de9)
        de10 = TemplateDocumentFactory(locale="de", parent=TemplateDocumentFactory())
        ApprovedRevisionFactory(document=de10)

        for i, doc in enumerate((d1, d2, d3, d4, d5, d6, d7, d8, d9, d10)):
            WikiDocumentVisits.objects.create(document=doc, visits=(100 + i), period=LAST_7_DAYS)

        for i, doc in enumerate((de1, de2, de3, de4, de5, de6, de7, de8, de9, de10)):
            WikiDocumentVisits.objects.create(document=doc, visits=(20 + i), period=LAST_7_DAYS)
            WikiDocumentVisits.objects.create(
                document=doc.parent, visits=(60 + i), period=LAST_7_DAYS
            )

    def test_get_featured_articles(self):
        with self.subTest("with defaults"):
            featured = get_featured_articles()
            self.assertEqual(len(featured), 4)
            self.assertEqual(
                set(d.id for d in featured),
                set([self.d1.id, self.d2.id, self.de1.parent.id, self.de2.parent.id]),
            )

        with self.subTest("with product"):
            featured = get_featured_articles(product=self.product1)
            self.assertEqual(len(featured), 3)
            self.assertEqual(
                set(d.id for d in featured), set([self.d1.id, self.d2.id, self.de1.parent.id])
            )

        with self.subTest("with product and topic"):
            featured = get_featured_articles(product=self.product1, topics=[self.topic2])
            self.assertEqual(len(featured), 2)
            self.assertEqual(set(d.id for d in featured), set([self.d2.id, self.de1.parent.id]))

        with self.subTest("with locale"):
            featured = get_featured_articles(locale="de")
            self.assertEqual(len(featured), 2)
            self.assertEqual(set(d.id for d in featured), set([self.de1.id, self.de2.id]))

        with self.subTest("with locale and product"):
            featured = get_featured_articles(locale="de", product=self.product2)
            self.assertEqual(len(featured), 1)
            self.assertEqual(featured[0].id, self.de2.id)

        with self.subTest("with locale and product and topic"):
            featured = get_featured_articles(
                locale="de", product=self.product1, topics=[self.topic1, self.topic2]
            )
            self.assertEqual(len(featured), 1)
            self.assertEqual(featured[0].id, self.de1.id)
