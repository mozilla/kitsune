import json
import time
from datetime import date, timedelta
from unittest import mock

from django.contrib.sessions.backends.base import SessionBase
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
    get_kb_visited,
    get_visible_document_or_404,
    has_visited_kb,
    num_active_contributors,
    remove_expired_from_kb_visited,
    update_kb_visited,
)
from django.http import Http404


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


class RemoveExpiredFromKBVisitedTests(TestCase):
    def setUp(self):
        self.session = SessionBase()

    def test_no_session(self):
        try:
            remove_expired_from_kb_visited(None)
        except Exception as err:
            self.fail(
                (
                    "remove_expired_from_kb_visited() raised an "
                    f"exception with a session of None: {err}"
                )
            )

    def test_session_without_kb_visited(self):
        remove_expired_from_kb_visited(self.session)
        self.assertFalse(self.session.modified)

    def test_session_with_empty_kb_visited(self):
        self.session["kb-visited"] = {}
        self.session.modified = False
        remove_expired_from_kb_visited(self.session)
        self.assertFalse(self.session.modified)

    def test_no_expired_slugs(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                "/en-US/kb/slug1": now,
                "/de/kb/slug2": now + 1,
            },
            "/mobile/privacy-and-security/": {
                "/it/kb/slug3": now + 2,
                "/fr/kb/slug4": now + 3,
            },
        }
        self.session.modified = False
        remove_expired_from_kb_visited(self.session, ttl=10)
        self.assertEqual(
            self.session["kb-visited"],
            {
                "/firefox/browse/": {
                    "/en-US/kb/slug1": now,
                    "/de/kb/slug2": now + 1,
                },
                "/mobile/privacy-and-security/": {
                    "/it/kb/slug3": now + 2,
                    "/fr/kb/slug4": now + 3,
                },
            },
        )
        self.assertFalse(self.session.modified)

    def test_remove_expired_slugs(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                "/en-US/kb/expired1": now - 20,
                "/en-US/kb/valid": now,
            },
            "/mobile/privacy-and-security/": {
                "/en-US/kb/expired2": now - 15,
                "/en-US/kb/expired3": now - 11,
            },
        }
        self.session.modified = False
        remove_expired_from_kb_visited(self.session, ttl=10)
        self.assertTrue(self.session.modified)
        self.assertEqual(
            self.session["kb-visited"],
            {
                "/firefox/browse/": {
                    "/en-US/kb/valid": now,
                },
            },
        )

    def test_all_slugs_expired(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                "/en-US/kb/expired1": now - 20,
                "/en-US/kb/expired2": now - 40,
            },
            "/mobile/privacy-and-security/": {
                "/en-US/kb/expired3": now - 15,
                "/en-US/kb/expired4": now - 11,
            },
        }
        self.session.modified = False
        remove_expired_from_kb_visited(self.session, ttl=10)
        self.assertTrue(self.session.modified)
        self.assertEqual(self.session["kb-visited"], {})


class UpdateKBVisitedTests(TestCase):
    def setUp(self):
        self.session = SessionBase()
        self.product1 = product1 = ProductFactory(slug="firefox")
        self.product2 = product2 = ProductFactory(slug="mobile")
        self.topic1 = topic1 = TopicFactory(slug="browse", products=[product1])
        self.topic2 = topic2 = TopicFactory(slug="settings", products=[product1, product2])
        self.doc1 = DocumentFactory(products=[product1], topics=[topic1])
        self.doc2 = DocumentFactory(products=[product1, product2], topics=[topic1, topic2])
        self.doc3 = DocumentFactory(locale="de", parent=self.doc1)

    def test_no_session(self):
        try:
            update_kb_visited(None, self.doc1)
        except Exception as err:
            self.fail(f"update_kb_visited() raised an exception with a session of None: {err}")

    def test_session_without_kb_visited(self):
        update_kb_visited(self.session, self.doc2)
        self.assertIn("kb-visited", self.session)
        key = "/firefox/mobile/browse/settings/"
        self.assertEqual(list(self.session["kb-visited"].keys()), [key])
        self.assertEqual(
            list(self.session["kb-visited"][key].keys()), [self.doc2.get_absolute_url()]
        )
        self.assertTrue(self.session.modified)

    def test_with_localized_document(self):
        update_kb_visited(self.session, self.doc3)
        self.assertIn("kb-visited", self.session)
        key = "/firefox/browse/"
        self.assertEqual(list(self.session["kb-visited"].keys()), [key])
        self.assertEqual(
            list(self.session["kb-visited"][key].keys()), [self.doc3.get_absolute_url()]
        )
        self.assertTrue(self.session.modified)

    def test_session_with_existing_kb_visited(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                "/en-US/kb/expired1": now - 20,
                "/en-US/kb/valid": now,
            },
            "/mobile/privacy-and-security/": {
                "/en-US/kb/expired2": now - 15,
                "/en-US/kb/expired3": now - 11,
            },
        }
        self.session.modified = False
        update_kb_visited(self.session, self.doc1, ttl=10)
        key = "/firefox/browse/"
        self.assertEqual(list(self.session["kb-visited"].keys()), [key])
        self.assertEqual(
            set(self.session["kb-visited"][key].keys()),
            set(["/en-US/kb/valid", self.doc1.get_absolute_url()]),
        )
        self.assertTrue(self.session.modified)


class GetKBVisitedTests(TestCase):
    def setUp(self):
        self.session = SessionBase()
        self.product1 = product1 = ProductFactory(slug="firefox")
        self.product2 = product2 = ProductFactory(slug="mobile")
        self.topic1 = topic1 = TopicFactory(slug="browse", products=[product1])
        self.topic2 = topic2 = TopicFactory(slug="settings", products=[product1, product2])
        self.doc1 = DocumentFactory(products=[product1], topics=[topic1])
        self.doc2 = DocumentFactory(products=[product1, product2], topics=[topic2])
        self.doc3 = DocumentFactory(locale="de", parent=self.doc1)

    def test_no_session(self):
        try:
            visits = get_kb_visited(None, self.product1, topic=self.topic1)
        except Exception as err:
            self.fail(f"get_kb_visited() raised an exception with a session of None: {err}")
        else:
            self.assertEqual(visits, [])

    def test_session_without_kb_visited(self):
        visits = get_kb_visited(self.session, self.product1)
        self.assertEqual(visits, [])
        self.assertFalse(self.session.modified)

    def test_session_with_empty_kb_visited(self):
        self.session["kb-visited"] = {}
        self.session.modified = False
        visits = get_kb_visited(self.session, self.product2)
        self.assertEqual(visits, [])
        self.assertFalse(self.session.modified)

    def test_with_product_1(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                self.doc1.get_absolute_url(): now,
                self.doc3.get_absolute_url(): now,
            },
            "/firefox/mobile/settings/": {
                self.doc2.get_absolute_url(): now - 15,
            },
        }
        self.session.modified = False
        visits = get_kb_visited(self.session, self.product1, ttl=10)
        self.assertEqual(
            set(visits), set([self.doc1.get_absolute_url(), self.doc3.get_absolute_url()])
        )
        self.assertEqual(
            self.session["kb-visited"],
            {
                "/firefox/browse/": {
                    self.doc1.get_absolute_url(): now,
                    self.doc3.get_absolute_url(): now,
                },
            },
        )
        self.assertTrue(self.session.modified)

    def test_with_product_2(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                self.doc1.get_absolute_url(): now,
                self.doc3.get_absolute_url(): now + 1,
            },
            "/firefox/mobile/settings/": {
                self.doc2.get_absolute_url(): now + 2,
            },
        }
        self.session.modified = False
        visits = get_kb_visited(self.session, self.product2, ttl=10)
        self.assertEqual(visits, [self.doc2.get_absolute_url()])
        self.assertEqual(
            self.session["kb-visited"],
            {
                "/firefox/browse/": {
                    self.doc1.get_absolute_url(): now,
                    self.doc3.get_absolute_url(): now + 1,
                },
                "/firefox/mobile/settings/": {
                    self.doc2.get_absolute_url(): now + 2,
                },
            },
        )
        self.assertFalse(self.session.modified)

    def test_with_product_and_topic_1(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                self.doc1.get_absolute_url(): now,
                self.doc3.get_absolute_url(): now - 15,
            },
            "/firefox/mobile/settings/": {
                self.doc2.get_absolute_url(): now + 2,
            },
        }
        self.session.modified = False
        visits = get_kb_visited(self.session, self.product1, topic=self.topic1, ttl=10)
        self.assertEqual(visits, [self.doc1.get_absolute_url()])
        self.assertEqual(
            self.session["kb-visited"],
            {
                "/firefox/browse/": {
                    self.doc1.get_absolute_url(): now,
                },
                "/firefox/mobile/settings/": {
                    self.doc2.get_absolute_url(): now + 2,
                },
            },
        )
        self.assertTrue(self.session.modified)

    def test_with_product_and_topic_2(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                self.doc1.get_absolute_url(): now,
                self.doc3.get_absolute_url(): now + 1,
            },
            "/firefox/mobile/settings/": {
                self.doc2.get_absolute_url(): now + 2,
            },
        }
        self.session.modified = False
        visits = get_kb_visited(self.session, self.product1, topic=self.topic2, ttl=10)
        self.assertEqual(visits, [self.doc2.get_absolute_url()])
        self.assertEqual(
            self.session["kb-visited"],
            {
                "/firefox/browse/": {
                    self.doc1.get_absolute_url(): now,
                    self.doc3.get_absolute_url(): now + 1,
                },
                "/firefox/mobile/settings/": {
                    self.doc2.get_absolute_url(): now + 2,
                },
            },
        )
        self.assertFalse(self.session.modified)

    def test_conversion_to_json(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                "/en-US/kb/stuff": now,
            },
            "/firefox/mobile/settings/": {
                "/en-US/kb/nonsense": now + 1,
            },
        }
        self.session.modified = False
        visits = get_kb_visited(self.session, self.product1, ttl=10)
        self.assertEqual(json.dumps(sorted(visits)), '["/en-US/kb/nonsense", "/en-US/kb/stuff"]')


class HasVisitedKBTests(TestCase):
    def setUp(self):
        self.session = SessionBase()
        self.product1 = product1 = ProductFactory(slug="firefox")
        self.product2 = product2 = ProductFactory(slug="mobile")
        self.topic1 = topic1 = TopicFactory(slug="browse", products=[product1])
        self.topic2 = topic2 = TopicFactory(slug="settings", products=[product1, product2])
        self.doc1 = DocumentFactory(products=[product1], topics=[topic1])
        self.doc2 = DocumentFactory(products=[product1, product2], topics=[topic2])
        self.doc3 = DocumentFactory(locale="de", parent=self.doc1)

    def test_no_session(self):
        try:
            result = has_visited_kb(None, self.product1, topic=self.topic1)
        except Exception as err:
            self.fail(f"get_kb_visited() raised an exception with a session of None: {err}")
        else:
            self.assertIs(result, False)

    def test_session_without_kb_visited(self):
        result = has_visited_kb(self.session, self.product1)
        self.assertIs(result, False)
        self.assertFalse(self.session.modified)

    def test_session_with_empty_kb_visited(self):
        self.session["kb-visited"] = {}
        self.session.modified = False
        result = has_visited_kb(self.session, self.product2)
        self.assertIs(result, False)
        self.assertFalse(self.session.modified)

    def test_with_product_1(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                self.doc1.get_absolute_url(): now,
                self.doc3.get_absolute_url(): now,
            },
            "/firefox/mobile/settings/": {
                self.doc2.get_absolute_url(): now - 15,
            },
        }
        self.session.modified = False
        result = has_visited_kb(self.session, self.product1, ttl=10)
        self.assertIs(result, True)
        self.assertEqual(
            self.session["kb-visited"],
            {
                "/firefox/browse/": {
                    self.doc1.get_absolute_url(): now,
                    self.doc3.get_absolute_url(): now,
                },
            },
        )
        self.assertTrue(self.session.modified)

    def test_with_product_2(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                self.doc1.get_absolute_url(): now,
                self.doc3.get_absolute_url(): now + 1,
            },
            "/firefox/mobile/settings/": {
                self.doc2.get_absolute_url(): now - 20,
            },
        }
        self.session.modified = False
        result = has_visited_kb(self.session, self.product2, ttl=10)
        self.assertIs(result, False)
        self.assertEqual(
            self.session["kb-visited"],
            {
                "/firefox/browse/": {
                    self.doc1.get_absolute_url(): now,
                    self.doc3.get_absolute_url(): now + 1,
                },
            },
        )
        self.assertTrue(self.session.modified)

    def test_with_product_and_topic_1(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                self.doc1.get_absolute_url(): now,
                self.doc3.get_absolute_url(): now - 15,
            },
            "/firefox/mobile/settings/": {
                self.doc2.get_absolute_url(): now + 2,
            },
        }
        self.session.modified = False
        result = has_visited_kb(self.session, self.product1, topic=self.topic1, ttl=10)
        self.assertIs(result, True)
        self.assertEqual(
            self.session["kb-visited"],
            {
                "/firefox/browse/": {
                    self.doc1.get_absolute_url(): now,
                },
                "/firefox/mobile/settings/": {
                    self.doc2.get_absolute_url(): now + 2,
                },
            },
        )
        self.assertTrue(self.session.modified)

    def test_with_product_and_topic_2(self):
        now = time.time()
        self.session["kb-visited"] = {
            "/firefox/browse/": {
                self.doc1.get_absolute_url(): now,
                self.doc3.get_absolute_url(): now + 1,
            },
            "/firefox/mobile/settings/": {
                self.doc2.get_absolute_url(): now + 2,
            },
        }
        self.session.modified = False
        result = has_visited_kb(self.session, self.product1, topic=self.topic2, ttl=10)
        self.assertIs(result, True)
        self.assertEqual(
            self.session["kb-visited"],
            {
                "/firefox/browse/": {
                    self.doc1.get_absolute_url(): now,
                    self.doc3.get_absolute_url(): now + 1,
                },
                "/firefox/mobile/settings/": {
                    self.doc2.get_absolute_url(): now + 2,
                },
            },
        )
        self.assertFalse(self.session.modified)


class GetVisibleDocumentTests(TestCase):
    def setUp(self):
        self.user = UserFactory()

        self.en_doc = ApprovedRevisionFactory(
            document__locale="en-US",
            document__slug="test-document",
            is_ready_for_localization=True,
        ).document

        self.de_rev = TranslatedRevisionFactory(
            document__locale="de",
            document__slug="test-document-de",
            document__parent=self.en_doc,
            based_on=self.en_doc.current_revision,
        )
        self.de_doc = self.de_rev.document

        self.fr_rev = TranslatedRevisionFactory(
            document__locale="fr",
            document__slug="test-document-fr",
            document__parent=self.en_doc,
            based_on=self.en_doc.current_revision,
        )
        self.fr_doc = self.fr_rev.document

    def test_get_document_by_locale_and_slug_direct_match(self):
        """Test getting a document when there's a direct match for locale and slug."""
        doc = get_visible_document_or_404(self.user, locale="en-US", slug="test-document")
        self.assertEqual(doc, self.en_doc)

        doc = get_visible_document_or_404(self.user, locale="de", slug="test-document-de")
        self.assertEqual(doc, self.de_doc)

        doc = get_visible_document_or_404(self.user, locale="fr", slug="test-document-fr")
        self.assertEqual(doc, self.fr_doc)

    def test_get_document_via_translation_for_nondefault_locale(self):
        """Test getting a document via its parent when no direct match in the requested locale."""
        with self.assertRaises(Http404):
            # This should raise a 404 because we're explicitly
            # setting look_for_translation_via_parent=False
            get_visible_document_or_404(
                self.user,
                locale="en-US",
                slug="test-document-de",
                look_for_translation_via_parent=False,
            )

        # This should also raise a 404 because cross-locale lookups should only work when
        # look_for_translation_via_parent is True
        with self.assertRaises(Http404):
            get_visible_document_or_404(self.user, locale="en-US", slug="test-document-de")

    def test_cross_locale_lookup(self):
        """Test the new cross-locale lookup functionality for language switcher."""
        doc = get_visible_document_or_404(
            self.user,
            locale="en-US",
            slug="test-document-de",
            look_for_translation_via_parent=True,
        )
        self.assertEqual(doc, self.en_doc)

        doc = get_visible_document_or_404(
            self.user,
            locale="en-US",
            slug="test-document-fr",
            look_for_translation_via_parent=True,
        )
        self.assertEqual(doc, self.en_doc)

        doc = get_visible_document_or_404(
            self.user, locale="de", slug="test-document", look_for_translation_via_parent=True
        )
        self.assertEqual(doc, self.de_doc)

        doc = get_visible_document_or_404(
            self.user, locale="de", slug="test-document-fr", look_for_translation_via_parent=True
        )
        self.assertEqual(doc, self.de_doc)

    def test_fallback_to_parent(self):
        """Test falling back to parent document when translation doesn't exist."""
        no_es_doc = ApprovedRevisionFactory(
            document__locale="en-US", document__slug="no-spanish"
        ).document

        with self.assertRaises(Http404):
            get_visible_document_or_404(
                self.user, locale="es", slug="no-spanish", look_for_translation_via_parent=True
            )

        doc = get_visible_document_or_404(
            self.user,
            locale="es",
            slug="no-spanish",
            look_for_translation_via_parent=True,
            return_parent_if_no_translation=True,
        )
        self.assertEqual(doc, no_es_doc)

    def test_nonexistent_document(self):
        """Test that we get a 404 for documents that don't exist in any locale."""
        with self.assertRaises(Http404):
            get_visible_document_or_404(
                self.user,
                locale="en-US",
                slug="doesnt-exist",
                look_for_translation_via_parent=True,
            )

        with self.assertRaises(Http404):
            get_visible_document_or_404(
                self.user, locale="de", slug="doesnt-exist", look_for_translation_via_parent=True
            )

    def test_unapproved_revision(self):
        """Test that users can't see documents without approved revisions."""
        unapproved_doc = RevisionFactory(
            document__locale="en-US", document__slug="unapproved", is_approved=False
        ).document

        random_user = UserFactory()
        with self.assertRaises(Http404):
            get_visible_document_or_404(random_user, locale="en-US", slug="unapproved")

        creator = unapproved_doc.revisions.first().creator
        doc = get_visible_document_or_404(creator, locale="en-US", slug="unapproved")
        self.assertEqual(doc, unapproved_doc)
