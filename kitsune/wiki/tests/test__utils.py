from datetime import date, timedelta

import mock
from nose.tools import eq_

from kitsune.products.tests import product
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import user
from kitsune.wiki.tests import revision, document
from kitsune.wiki.utils import (active_contributors, num_active_contributors,
                                generate_short_url)

from django.test.utils import override_settings


class ActiveContributorsTestCase(TestCase):

    def setUp(self):
        super(ActiveContributorsTestCase, self).setUp()

        start_date = date.today() - timedelta(days=10)
        self.start_date = start_date
        before_start = start_date - timedelta(days=1)

        # Create some revisions to test with.

        # 3 'en-US' contributors:
        d = document(locale='en-US', save=True)
        u = user(save=True)
        self.user = u
        revision(document=d, is_approved=True, reviewer=u, save=True)
        revision(document=d, creator=u, save=True)

        self.product = product(save=True)
        r = revision(created=start_date, save=True)
        r.document.products.add(self.product)

        # Add one that shouldn't count:
        self.en_us_old = revision(document=d, created=before_start, save=True)

        # 4 'es' contributors:
        d = document(locale='es', save=True)
        revision(document=d, is_approved=True, reviewer=u, save=True)
        revision(document=d, creator=u, reviewer=user(save=True), save=True)
        revision(document=d, created=start_date, save=True)
        revision(document=d, save=True)
        # Add one that shouldn't count:
        self.es_old = revision(document=d, created=before_start, save=True)

    def test_active_contributors(self):
        """Test the active_contributors util method."""
        start_date = self.start_date

        en_us_contributors = active_contributors(
            from_date=start_date, locale='en-US')
        es_contributors = active_contributors(
            from_date=start_date, locale='es')
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

        eq_(3, num_active_contributors(from_date=start_date, locale='en-US'))
        eq_(4, num_active_contributors(from_date=start_date, locale='es'))
        eq_(6, num_active_contributors(from_date=start_date))
        eq_(1, num_active_contributors(
            from_date=start_date, product=self.product))
        eq_(1, num_active_contributors(
            from_date=start_date, locale='en-US', product=self.product))
        eq_(0, num_active_contributors(
            from_date=start_date, locale='es', product=self.product))


@override_settings(BITLY_LOGIN='test', BITLY_API_KEY='test-apikey')
class GenerateShortUrlTestCase(TestCase):

    def setUp(self):
        self.test_url = ('https://support.mozilla.org/en-US/kb/'
                         'update-firefox-latest-version')

    @mock.patch('kitsune.wiki.utils.requests')
    def test_generate_short_url_200(self, mock_requests):
        """Tests a valid 200 response for generate_short_url method."""
        mock_json = mock.Mock()
        mock_json.json.return_value = {
            'status_code': 200,
            'data': {
                'url': 'http://mzl.la/LFolSf'
            }
        }
        mock_requests.post.return_value = mock_json
        eq_('http://mzl.la/LFolSf', generate_short_url(self.test_url))

    @mock.patch('kitsune.wiki.utils.requests')
    def test_generate_short_url_401(self, mock_requests):
        """Tests a valid 401 response for generate_short_url method."""
        mock_json = mock.Mock()
        mock_json.json.return_value = {'status_code': 401}
        mock_requests.post.return_value = mock_json
        self.assertRaises(Exception, generate_short_url, self.test_url)

    @mock.patch('kitsune.wiki.utils.requests')
    def test_generate_short_url_403(self, mock_requests):
        """Tests a valid 403 response for generate_short_url method."""
        mock_json = mock.Mock()
        mock_json.json.return_value = {'status_code': 403}
        mock_requests.post.return_value = mock_json
        self.assertRaises(Exception, generate_short_url, self.test_url)

    @mock.patch('kitsune.wiki.utils.requests')
    def test_generate_short_url_other(self, mock_requests):
        """Tests aany other valid response for generate_short_url method."""
        mock_json = mock.Mock()
        mock_json.json.return_value = {'status_code': 500}
        mock_requests.post.return_value = mock_json
        self.assertRaises(Exception, generate_short_url, self.test_url)
