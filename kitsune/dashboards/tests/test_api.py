import json
from datetime import date, timedelta

from nose.tools import eq_

from kitsune.dashboards.tests import wikimetric
from kitsune.products.tests import product
from kitsune.sumo.helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


class WikiMetricAPITests(TestCase):

    def test_default(self):
        """Test the default API call (no filtering)."""
        today = date.today()

        # Create 10 wikimetrics.
        for i in range(10):
            wikimetric(
                code='awesomeness_%s' % i,
                date=today - timedelta(days=i),
                value=i,
                save=True)

        # Call the API.
        response = self.client.get(
            urlparams(reverse('api.wikimetric_list'), format='json'))
        eq_(200, response.status_code)

        results = json.loads(response.content)['results']

        # Verify the results are what we created.
        eq_(10, len(results))
        for i in range(10):
            result = results[i]
            eq_(i, result['value'])
            eq_('awesomeness_%s' % i, result['code'])
            eq_(str(today - timedelta(days=i)), result['date'])

    def test_product_filter(self):
        """Test filtering results by product."""
        today = date.today()

        # Create products and associated wiki metrics.
        p1 = product(save=True)
        p2 = product(save=True)

        # Create 3 for each product:
        for i in range(3):
            for p in [p1, p2]:
                wikimetric(
                    date=today - timedelta(days=i),
                    product=p,
                    save=True)
        # Create one more for p2.
        wikimetric(
            date=today - timedelta(days=4),
            product=p2,
            save=True)

        # Call and verify the API for product=p1.
        response = self.client.get(
            urlparams(reverse('api.wikimetric_list'), format='json',
                      product=p1.slug))
        eq_(200, response.status_code)

        results = json.loads(response.content)['results']
        eq_(3, len(results))

        # Call and verify the API for product=p1.
        response = self.client.get(
            urlparams(reverse('api.wikimetric_list'), format='json',
                      product=p2.slug))
        eq_(200, response.status_code)

        results = json.loads(response.content)['results']
        eq_(4, len(results))

    def test_locale_filter(self):
        """Test filtering results by locale."""
        today = date.today()

        # Create 3 wikimetrics for es:
        for i in range(3):
            wikimetric(
                locale='es',
                date=today - timedelta(days=i),
                save=True)

        # Create 1 for fr:
        wikimetric(locale='fr', save=True)

        # Call and verify the API for locale=es.
        response = self.client.get(
            urlparams(reverse('api.wikimetric_list'), format='json',
                      locale='es'))
        eq_(200, response.status_code)

        results = json.loads(response.content)['results']
        eq_(3, len(results))

         # Call and verify the API for locale=fr.
        response = self.client.get(
            urlparams(reverse('api.wikimetric_list'), format='json',
                      locale='fr'))
        eq_(200, response.status_code)

        results = json.loads(response.content)['results']
        eq_(1, len(results))

    def test_code_filter(self):
        """Test filtering results by code."""
        today = date.today()

        # Create 3 wikimetrics for active_contributors:
        for i in range(3):
            wikimetric(
                code='active_contributors',
                date=today - timedelta(days=i),
                save=True)

        # Create 1 for percent_localized_all:
        wikimetric(code='percent_localized_all', save=True)

        # Call and verify the API for code=active_contributors.
        response = self.client.get(
            urlparams(reverse('api.wikimetric_list'), format='json',
                      code='active_contributors'))
        eq_(200, response.status_code)

        results = json.loads(response.content)['results']
        eq_(3, len(results))

        # Call and verify the API for code=percent_localized_all.
        response = self.client.get(
            urlparams(reverse('api.wikimetric_list'), format='json',
                      code='percent_localized_all'))
        eq_(200, response.status_code)

        results = json.loads(response.content)['results']
        eq_(1, len(results))
