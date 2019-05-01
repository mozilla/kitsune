from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.products.tests import ProductFactory
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import TestCaseBase


class HomeTestCase(ElasticTestCase):
    def test_home(self):
        """Verify that home page renders products."""

        # Create some topics and products
        ProductFactory.create_batch(4)

        # GET the home page and verify the content
        r = self.client.get(reverse('home'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(4, len(doc('#products-and-services li')))


# TO DO
# These tests could be part of HomeTestCase, but HomeTestCase is
# not being run in the test suite because ElasticTestCase's are
# excluded in run-unit-tests.sh
class TestFxaNotifications(TestCaseBase):
    def test_no_fxa_notification(self):
        response = self.client.get(reverse('home'), follow=True)
        doc = pq(response.content)
        eq_(0, len(doc('#fxa-notification-updated')))
        eq_(0, len(doc('#fxa-notification-created')))

    def test_fxa_notification_updated_is_visible(self):
        session = self.client.session
        session['fxa_notification'] = 'updated'
        session.save()
        response = self.client.get(reverse('home'), follow=True)
        doc = pq(response.content)
        eq_(1, len(doc('#fxa-notification-updated')))

    def test_fxa_notification_created_is_visible(self):
        session = self.client.session
        session['fxa_notification'] = 'created'
        session.save()
        response = self.client.get(reverse('home'), follow=True)
        doc = pq(response.content)
        eq_(1, len(doc('#fxa-notification-created')))
