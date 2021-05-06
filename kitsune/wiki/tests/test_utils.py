from datetime import date, timedelta

from unittest import mock
from nose.tools import eq_

from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import RevisionFactory, DocumentFactory
from kitsune.wiki.utils import (
    BitlyUnauthorizedException,
    BitlyRateLimitException,
    BitlyException,
    active_contributors,
    num_active_contributors,
    generate_short_url,
)

from django.test.utils import override_settings


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
        eq_(3, len(en_us_contributors))
        assert self.user in en_us_contributors
        assert self.en_us_old.creator not in en_us_contributors

        eq_(4, len(es_contributors))
        assert self.user in es_contributors
        assert self.es_old.creator not in es_contributors

        eq_(6, len(all_contributors))
        assert self.user in all_contributors
        assert self.en_us_old.creator not in all_contributors
        assert self.es_old.creator not in all_contributors

    def test_num_active_contributors(self):
        """Test the num_active_contributors util method."""
        start_date = self.start_date

        eq_(3, num_active_contributors(from_date=start_date, locale="en-US"))
        eq_(4, num_active_contributors(from_date=start_date, locale="es"))
        eq_(6, num_active_contributors(from_date=start_date))
        eq_(1, num_active_contributors(from_date=start_date, product=self.product))
        eq_(1, num_active_contributors(from_date=start_date, locale="en-US", product=self.product))
        eq_(0, num_active_contributors(from_date=start_date, locale="es", product=self.product))


@override_settings(BITLY_LOGIN="test", BITLY_API_KEY="test-apikey")
class GenerateShortUrlTestCase(TestCase):
    def setUp(self):
        self.test_url = "https://support.mozilla.org/en-US/kb/update-firefox-latest-version"

    @mock.patch("kitsune.wiki.utils.requests")
    def test_generate_short_url_200(self, mock_requests):
        """Tests a valid 200 response for generate_short_url method."""
        mock_json = mock.Mock()
        mock_json.json.return_value = {"status_code": 200, "data": {"url": "http://mzl.la/LFolSf"}}
        mock_requests.post.return_value = mock_json
        eq_("http://mzl.la/LFolSf", generate_short_url(self.test_url))

    @mock.patch("kitsune.wiki.utils.requests")
    def test_generate_short_url_401(self, mock_requests):
        """Tests a valid 401 response for generate_short_url method."""
        mock_json = mock.Mock()
        mock_json.json.return_value = {"status_code": 401}
        mock_requests.post.return_value = mock_json
        self.assertRaises(BitlyUnauthorizedException, generate_short_url, self.test_url)

    @mock.patch("kitsune.wiki.utils.requests")
    def test_generate_short_url_403(self, mock_requests):
        """Tests a valid 403 response for generate_short_url method."""
        mock_json = mock.Mock()
        mock_json.json.return_value = {"status_code": 403}
        mock_requests.post.return_value = mock_json
        self.assertRaises(BitlyRateLimitException, generate_short_url, self.test_url)

    @mock.patch("kitsune.wiki.utils.requests")
    def test_generate_short_url_other(self, mock_requests):
        """Tests any other valid response for generate_short_url method."""
        mock_json = mock.Mock()
        mock_json.json.return_value = {"status_code": 500}
        mock_requests.post.return_value = mock_json
        self.assertRaises(BitlyException, generate_short_url, self.test_url)
